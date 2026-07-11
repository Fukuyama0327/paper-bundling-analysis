# -*- coding: utf-8 -*-
"""fig:optimization_results と tab:optimization_results の生成（cell 34, 41相当）。

入力は厳密な閉形式値で再評価済みの最適化結果CSV
（`reevaluate_optimization_objectives.py` の出力、ObjectiveValue_Exact列必須）。
D別に最小のObjectiveValue_Exactを持つ行を採り、
(1) D vs 最適目的関数値の折れ線図（fig:optimization_results）、
(2) 現行管理（管理者ベース）比較のLaTeX表（tab:optimization_results）を出力する。

管理者ベースの基準値は `--bridges`（322橋CSV）から閉形式で計算する。
注意（2026-07-06確認）: 現行main.texの基準値2.5241は秋大会旧系列の
フィッティング式 f(N)=1.594N/(128.7+N) 由来で、最適化行（新閉形式系列）と
不整合。本スクリプトは基準値も同じ閉形式・同じqで計算し、系列を統一する
（q更新後の基準値は約2.5883）。

使用例:
    python scripts/plot_optimization_results.py \
        --input outputs/optimization_results_exact_objective.csv \
        --bridges data/processed/target_rc_bridges_322.csv \
        --output-stem figures/optimization_results
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.expected_contracts import (
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)
from bundling_analysis.plotting_utils import setup_japanese_font


def admin_objective(bridges_csv: Path, bundle_limit: int, repair_probability: float) -> tuple[float, pd.Series]:
    """管理者ベース（1管理者=1地域）の閉形式目的関数値を計算する。"""
    df = pd.read_csv(bridges_csv)
    counts = df["管理者"].value_counts()
    total = sum(expected_contracts(int(n), bundle_limit, repair_probability) for n in counts)
    return total, counts


def best_per_distance(df: pd.DataFrame) -> pd.DataFrame:
    """D別に最小のObjectiveValue_Exactを持つ行を返す。"""
    if "ObjectiveValue_Exact" not in df.columns:
        raise ValueError("入力CSVに ObjectiveValue_Exact 列がありません。"
                         "reevaluate_optimization_objectives.py の出力を渡してください。")
    idx = df.groupby("MaxDistance")["ObjectiveValue_Exact"].idxmin()
    return df.loc[idx].sort_values("MaxDistance").reset_index(drop=True)


def plot_best_objective(best: pd.DataFrame, output_stem: Path) -> list[Path]:
    """D vs 最適目的関数値の折れ線図を保存する（cell 34スタイル）。"""
    setup_japanese_font()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(best["MaxDistance"], best["ObjectiveValue_Exact"], marker="o", linestyle="-")
    ax.set_xlabel("距離制約 D [km]")
    ax.set_ylabel("目的関数値（最適）")
    ax.grid(True)
    fig.tight_layout()
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        paths.append(path)
    plt.close(fig)
    return paths


def to_latex_rows(best: pd.DataFrame, baseline: float) -> str:
    """tab:optimization_results のtabular行を生成する（D≥40のM=1行は集約）。"""
    lines = [f"既存の管理 & {baseline:.4f} & 0.0\\% \\\\"]
    merged_from = None
    prev_obj = None
    rows = list(best.itertuples(index=False))
    for i, row in enumerate(rows):
        d = float(row.MaxDistance)
        m = int(row.M)
        obj = float(row.ObjectiveValue_Exact)
        # 末尾で同一値（全域1地域等）が続く場合は「D >= x km」と集約
        rest = rows[i:]
        if (
            len(rest) > 1
            and all(abs(float(r.ObjectiveValue_Exact) - obj) < 1e-9 and int(r.M) == m for r in rest)
        ):
            reduction = (1 - obj / baseline) * 100
            lines.append(
                f"\\(D \\geq {d:.0f}\\) km, \\(M={m}\\) & {obj:.4f} & {reduction:.1f}\\% \\\\"
            )
            break
        reduction = (1 - obj / baseline) * 100
        lines.append(f"\\(D={d:.0f}\\) km, \\(M={m}\\) & {obj:.4f} & {reduction:.1f}\\% \\\\")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path,
                        default=Path("data/processed/optimization_results_exact_objective.csv"))
    parser.add_argument("--bridges", type=Path,
                        default=Path("data/processed/target_rc_bridges_322.csv"))
    parser.add_argument("--bundle-limit", type=int, default=5)
    parser.add_argument("--output-stem", type=Path, default=Path("figures/optimization_results"))
    parser.add_argument("--table-output", type=Path,
                        default=Path("outputs/optimization_results_table.csv"))
    args = parser.parse_args()

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    baseline, counts = admin_objective(args.bridges, args.bundle_limit, q)
    print(f"q = {q!r}, L = {args.bundle_limit}")
    print(f"管理者ベース基準値 = {baseline:.6f}（管理者別橋梁数: {counts.to_dict()}）")

    df = pd.read_csv(args.input)
    best = best_per_distance(df)
    print(best[["MaxDistance", "M", "ObjectiveValue_Exact"]].to_string(index=False))

    for path in plot_best_objective(best, args.output_stem):
        print(f"保存: {path}")

    table = best[["MaxDistance", "M", "ObjectiveValue_Exact"]].copy()
    table["Reduction(%)"] = (1 - table["ObjectiveValue_Exact"] / baseline) * 100
    baseline_row = pd.DataFrame(
        [{"MaxDistance": None, "M": None, "ObjectiveValue_Exact": baseline, "Reduction(%)": 0.0}]
    )
    args.table_output.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([baseline_row, table], ignore_index=True).to_csv(args.table_output, index=False)
    print(f"保存: {args.table_output}")

    print("\n--- main.tex 用 LaTeX 行（tab:optimization_results）---")
    print(to_latex_rows(best, baseline))


if __name__ == "__main__":
    main()
