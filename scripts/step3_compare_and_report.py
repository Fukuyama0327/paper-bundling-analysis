# -*- coding: utf-8 -*-
"""STEP3-5: 管理者グループとの比較・目的関数成分分析。

`20251206.ipynb` cell 39（目的関数成分分析）・cell 40（管理者グループ比較）の
再実装。z_assignments.pkl のレガシーフォーマット分岐（7-2章-7）は廃止し、
`run_gurobi_districting.py` の solutions pkl と、ノートブック新形式
（by_distance キー付きdict）の2形式のみ対応する。

補修確率qと期待契約件数は `expected_contracts.py`（cell 26 と同一の一般
アルゴリズムに統一済み）を使用する。

使用例:
    python scripts/step3_compare_and_report.py \
        --bridges data/processed/target_rc_bridges_322.csv \
        --distance-matrix data/processed/distance_matrix_322_20251208.pkl \
        --solutions outputs/gurobi_districting_validation_solutions.pkl \
        --output outputs/comparison_report.csv
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.expected_contracts import (
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)


def region_max_distances(assignment: np.ndarray, d_matrix: np.ndarray) -> list[float]:
    """各地域内の最大橋梁間距離を返す。"""
    result = []
    for m in range(assignment.shape[1]):
        members = np.where(assignment[:, m] == 1)[0]
        if len(members) > 1:
            sub = d_matrix[np.ix_(members, members)]
            result.append(float(sub.max()))
        else:
            result.append(0.0)
    return result


def objective_from_assignment(
    assignment: np.ndarray, bundle_limit: int, repair_probability: float
) -> tuple[float, list[int]]:
    """割当行列から厳密な閉形式目的関数値と地域別橋梁数を計算する。"""
    counts = [int(assignment[:, m].sum()) for m in range(assignment.shape[1])]
    total = sum(expected_contracts(c, bundle_limit, repair_probability) for c in counts)
    return total, counts


def admin_baseline(
    df: pd.DataFrame,
    d_matrix: np.ndarray,
    bundle_limit: int,
    repair_probability: float,
    admin_col: str = "管理者",
) -> dict:
    """現行の管理者ベース地域分割を1地域=1管理者として評価する（cell 40）。"""
    admins = df[admin_col].astype(str).to_numpy()
    groups = list(dict.fromkeys(admins))
    n = len(df)
    assignment = np.zeros((n, len(groups)), dtype=int)
    for i, admin in enumerate(groups):
        assignment[np.where(admins == admin)[0], i] = 1
    total, counts = objective_from_assignment(assignment, bundle_limit, repair_probability)
    return {
        "label": f"管理者ベース（{len(groups)}グループ）",
        "M": len(groups),
        "objective": total,
        "counts": counts,
        "max_distances": region_max_distances(assignment, d_matrix),
    }


def load_solutions(path: Path) -> dict[tuple[float, int], np.ndarray]:
    """solutions pkl を {(D, M): assignment} に正規化して読み込む。

    対応形式:
      1. `run_gurobi_districting.py` 形式: {(D, M): {'assignment': ..., ...}}
      2. ノートブック新形式: {'by_distance': {D: {M: assignment}}, ...}
    """
    with path.open("rb") as f:
        data = pickle.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"未対応のpkl形式です: {type(data)}")
    if "by_distance" in data:
        return {
            (float(d), int(m)): np.asarray(z)
            for d, per_m in data["by_distance"].items()
            for m, z in per_m.items()
        }
    normalized = {}
    for key, value in data.items():
        d, m = key
        assignment = value["assignment"] if isinstance(value, dict) else value
        normalized[(float(d), int(m))] = np.asarray(assignment)
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bridges", required=True, help="対象橋梁CSV（管理者列必須）")
    parser.add_argument("--distance-matrix", required=True, help="距離行列pkl（{'order','d_core'}）")
    parser.add_argument("--solutions", required=True, help="最適化割当pkl")
    parser.add_argument("--bundle-limit", type=int, default=5, help="契約バンドリング上限 L")
    parser.add_argument("--output", required=True, help="比較結果CSVの出力パス")
    args = parser.parse_args()

    df = pd.read_csv(args.bridges)
    with Path(args.distance_matrix).open("rb") as f:
        dist_data = pickle.load(f)
    d_matrix = np.asarray(dist_data["d_core"], dtype=float)
    if len(df) != d_matrix.shape[0]:
        raise ValueError(
            f"橋梁数 {len(df)} と距離行列サイズ {d_matrix.shape[0]} が一致しません。"
        )

    # 割当行列（run_gurobi_districting.py の出力）と d_matrix はどちらも pkl の
    # order の並びを前提とする。CSVの行順は order と異なりうる（実データでは
    # 座標順ソート済みのため実際に異なる）ので、CSV側を order に並べ替えて
    # admin_baseline の行番号を d_matrix・割当行列と揃える。
    order = [str(x) for x in dist_data.get("order", [])]
    if order:
        if "shisetsu_id" not in df.columns:
            raise ValueError(
                "橋梁CSVに shisetsu_id 列がなく、距離行列pklのorderと突き合わせできません。"
                "step3_filter_target_municipalities.py の出力を渡してください。"
            )
        ids = df["shisetsu_id"].astype(str).tolist()
        if sorted(ids) != sorted(order):
            raise ValueError(
                "橋梁CSVの shisetsu_id と距離行列pklの order が同じ集合ではありません。"
                "入力の組み合わせを確認してください。"
            )
        if ids != order:
            df = (
                df.assign(_sid=df["shisetsu_id"].astype(str))
                .set_index("_sid")
                .loc[order]
                .reset_index(drop=True)
            )
            print("注意: 橋梁CSVの行順を距離行列pklのorderに合わせて並べ替えました。")

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    print(f"補修確率 q = {q!r}, L = {args.bundle_limit}")

    rows = []
    baseline = admin_baseline(df, d_matrix, args.bundle_limit, q)
    rows.append(
        {
            "Case": baseline["label"],
            "MaxDistance": np.nan,
            "M": baseline["M"],
            "ObjectiveValue_Exact": baseline["objective"],
            "RegionCounts": ";".join(map(str, baseline["counts"])),
            "MaxDistanceWithin": max(baseline["max_distances"]),
        }
    )
    print(f"管理者ベース: M={baseline['M']}, 目的関数値={baseline['objective']:.6f}")

    solutions = load_solutions(Path(args.solutions))
    for (d_threshold, m), assignment in sorted(solutions.items()):
        total, counts = objective_from_assignment(assignment, args.bundle_limit, q)
        max_within = max(region_max_distances(assignment, d_matrix))
        improvement = (baseline["objective"] - total) / baseline["objective"] * 100
        rows.append(
            {
                "Case": f"最適化 D={d_threshold}km, M={m}",
                "MaxDistance": d_threshold,
                "M": m,
                "ObjectiveValue_Exact": total,
                "RegionCounts": ";".join(map(str, counts)),
                "MaxDistanceWithin": max_within,
                "ImprovementVsAdmin(%)": round(improvement, 3),
            }
        )
        print(
            f"D={d_threshold}km, M={m}: 目的関数値={total:.6f} "
            f"(管理者比 {improvement:+.2f}%), 地域内最大距離={max_within:.2f}km"
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
