# -*- coding: utf-8 -*-
"""STEP3-3b: eMarkov推定の実行（markov_input TSV → 推移確率行列・q）。

`20251206.ipynb` cell 19（run_emarkovラッパー）・cell 22（シナリオ実行）の
再実装。`step3_prepare_markov_input.py` が出力したTSVを読み、eMarkov推定を
実行して推移確率行列（全段階＋3×3正規化版）とqを保存する。

推定設定はcell 19と同一（MATLAB互換: matlab_convergence=True,
scaling_method="max", final_iter_no_ridge=3, 切片のみの設計行列）。

出力（--output-dir/<scenario>/ 配下）:
  - <scenario>_transition_matrix.csv 等（save_emarkov_result による一式）
  - <scenario>_transition_matrix_stage3.csv（Stage4をStage3に吸収した3×3）
  - <scenario>_repair_probability.json（3×3行列から計算したq）
  - 実行引数・入力ファイルは --output-dir/emarkov_run.meta.json に記録

使用例:
    python scripts/step3_run_emarkov.py \
        --input-dir data/processed/markov_input \
        --scenarios with_supply_collapse \
        --output-dir outputs/emarkov_results
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.emarkov_estimator import (
    EMarkovEstimator,
    build_design_matrix,
    save_emarkov_result,
)
from bundling_analysis.expected_contracts import repair_probability_from_transition_matrix
from bundling_analysis.preprocessing import hantei_to_int

ALL_SCENARIOS = [
    "without_supply",
    "without_supply_collapse",
    "with_supply",
    "with_supply_collapse",
]


def load_markov_input(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """markov_input TSVから before/after/interval のint配列を読み込む。"""
    df = pd.read_csv(path, sep="\t", encoding="utf-8-sig")
    required = {"before", "after", "interval"}
    if not required.issubset(df.columns):
        raise RuntimeError(f"{path}: 必要列が不足しています: {required - set(df.columns)}")
    before = df["before"].apply(hantei_to_int)
    after = df["after"].apply(hantei_to_int)
    interval = pd.to_numeric(df["interval"], errors="coerce")
    if before.isna().any() or after.isna().any() or interval.isna().any():
        raise RuntimeError(f"{path}: before/after/interval に数値化できない値があります。")
    return (
        before.astype(int).to_numpy(),
        after.astype(int).to_numpy(),
        interval.astype(int).to_numpy(),
    )


def collapse_to_stage3(transition_matrix: np.ndarray) -> np.ndarray:
    """Stage4以降をStage3に吸収した3×3行列を作り行方向に正規化する（cell 19）。"""
    if transition_matrix.shape[0] < 3:
        raise ValueError("3段階未満の行列は折り畳めません。")
    p_stage3 = transition_matrix[:3, :3].copy()
    if transition_matrix.shape[1] >= 4:
        p_stage3[:, -1] += transition_matrix[:3, 3:].sum(axis=1)
    row_sums = p_stage3.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return p_stage3 / row_sums


def run_scenario(
    input_path: Path,
    scenario: str,
    output_dir: Path,
    max_iter: int,
    tol: float,
    verbose: bool,
) -> dict:
    """1シナリオ分のeMarkov推定を実行し、結果サマリー辞書を返す。"""
    before, after, interval = load_markov_input(input_path)
    print(f"=== {scenario}: {len(before):,} 遷移 ===")

    design_matrix, _ = build_design_matrix(len(before), include_intercept=True)
    estimator = EMarkovEstimator(
        max_iter=max_iter,
        tol=tol,
        matlab_convergence=True,
        scaling_method="max",
        final_iter_no_ridge=3,
        verbose=verbose,
        ll_epsilon=1e-300,
    )
    result = estimator.fit(before, after, interval, design_matrix)

    save_dir = output_dir / scenario
    save_dir.mkdir(parents=True, exist_ok=True)
    save_emarkov_result(result, str(save_dir), prefix=scenario)

    full = np.asarray(result.transition_matrix, dtype=float)
    print(f"推移確率行列（全段階 {full.shape[0]}×{full.shape[1]}）:")
    print(np.array_str(full, precision=6, suppress_small=True))

    summary = {
        "scenario": scenario,
        "input": str(input_path),
        "n_transitions": int(len(before)),
        "matrix_size": list(full.shape),
        "log_likelihood": float(result.log_likelihood),
        "aic": float(result.aic),
        "iterations": int(result.iterations),
    }

    # 3×3（Stage3吸収）版とq。行列が既に3×3ならそのまま使う。
    p3 = full if full.shape == (3, 3) else collapse_to_stage3(full)
    p3_path = save_dir / f"{scenario}_transition_matrix_stage3.csv"
    np.savetxt(p3_path, p3, delimiter=",")
    _, q = repair_probability_from_transition_matrix(p3.tolist())
    print(f"3×3行列（Stage3吸収）→ q = {q!r}")
    with (save_dir / f"{scenario}_repair_probability.json").open("w", encoding="utf-8") as f:
        json.dump({"q": q, "stage3_matrix": p3.tolist()}, f, ensure_ascii=False, indent=2)
    summary["q_stage3"] = q
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", required=True,
                        help="markov_input_<scenario>.txt があるディレクトリ")
    parser.add_argument("--scenarios", nargs="+", default=ALL_SCENARIOS,
                        choices=ALL_SCENARIOS, help="実行するシナリオ（デフォルト: 全4種）")
    parser.add_argument("--output-dir", required=True, help="結果の出力ディレクトリ")
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--tol", type=float, default=1e-6)
    parser.add_argument("--verbose", action="store_true", help="反復ログを表示")
    args = parser.parse_args()

    print("=== 実行パラメータ ===")
    for key, value in sorted(vars(args).items()):
        print(f"  {key}: {value}")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for scenario in args.scenarios:
        input_path = input_dir / f"markov_input_{scenario}.txt"
        if not input_path.exists():
            print(f"警告: {input_path} が見つからないためスキップします。")
            continue
        summaries.append(
            run_scenario(input_path, scenario, output_dir,
                         args.max_iter, args.tol, args.verbose)
        )

    metadata = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "args": {k: str(v) for k, v in vars(args).items()},
        "results": summaries,
    }
    meta_path = output_dir / "emarkov_run.meta.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
