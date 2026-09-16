"""Tabulate the realized maximum within-area distance R(x*) of each optimized solution.

The manuscript reports only the imposed distance limit ``D``. A reviewer asked for
the *realized* maximum within-area distance as well, so that varying ``D`` traces the
nondominated relationship between ``Z(x*)`` and ``R(x*)`` directly, without the
unit-dependent weight alpha of Eq. (17).

For management area ``k`` the diameter is

    R_k(x) = max{ d_ij : i, j assigned to k },     R(x) = max_k R_k(x),

with ``R_k = 0`` for an area holding a single bridge. Distances come from the same
great-circle (haversine) matrix the MIP was solved with, so ``R(x*)`` is exactly the
quantity the fourth constraint of Eq. (19) bounds.

Nothing has to be re-solved: ``run_gurobi_districting.py`` already stores the
assignment matrix of every case, so ``R_k`` is a lookup in the distance matrix.

The output carries one row per optimized case plus one row for the current
administrative districting (bridges grouped by their managing municipality), which
is the baseline the reduction column is measured against.

Note that Eq. (18) does not minimize ``R(x)`` among assignments sharing the optimal
objective value, so ``R(x*)`` is what the solver happened to return, not the smallest
realized distance attaining ``Z(x*)``. Expect ``R(x*)`` to sit just under ``D``.

Usage:
    python scripts/compute_realized_radius.py --output outputs/realized_radius.csv
"""

from __future__ import annotations

import argparse
import csv
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

FIELDNAMES = [
    "Districting",
    "MaxDistance",
    "M",
    "BundleLimit",
    "ObjectiveValue_Exact",
    "RealizedRadius",
    "Slack_D_minus_R",
    "Reduction(%)",
    "ElapsedSeconds",
    "Nondominated",
    "RegionDiameters",
    "RegionCounts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tabulate realized max within-area distance R(x*) per optimized case."
    )
    parser.add_argument(
        "--solutions",
        type=Path,
        default=Path("data/processed/districting_solutions_all36.pkl"),
        help="Solutions pickle written by run_gurobi_districting.py --solutions-output.",
    )
    parser.add_argument(
        "--distance-matrix",
        type=Path,
        default=Path("data/processed/distance_matrix_322_20251208.pkl"),
        help="Pickle containing {'order': ..., 'd_core': distance_matrix}.",
    )
    parser.add_argument(
        "--bridges",
        type=Path,
        default=Path("data/processed/target_rc_bridges_322.csv"),
        help=(
            "Target bridge CSV. Supplies the current administrative districting row "
            "(grouped by 管理者) and hence the baseline of the Reduction(%%) column. "
            "That baseline depends on L, so it cannot be hard-coded once a bundle "
            "limit other than 5 is analysed."
        ),
    )
    parser.add_argument("--bundle-limit", type=int, default=5, help="Bundle limit L.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/realized_radius.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the cross-check of recomputed counts/objective against each stored row.",
    )
    return parser.parse_args()


def load_distance_matrix(path: Path) -> tuple[dict[str, int], np.ndarray]:
    with path.open("rb") as f:
        data = pickle.load(f)
    order = [str(item) for item in data["order"]]
    matrix = np.asarray(data["d_core"], dtype=float)
    if matrix.shape != (len(order), len(order)):
        raise SystemExit("distance matrix shape does not match order length")
    return {name: index for index, name in enumerate(order)}, matrix


def diameter(rows: np.ndarray, distance_matrix: np.ndarray) -> float:
    """Largest pairwise distance within one area; 0 for a single-bridge area."""
    if len(rows) < 2:
        return 0.0
    return float(distance_matrix[np.ix_(rows, rows)].max())


def nondominated(points: list[tuple[float, float]]) -> list[bool]:
    """Minimize both coordinates. Ties on both coordinates stay mutually nondominated."""
    flags = []
    for i, (radius_i, objective_i) in enumerate(points):
        dominated = any(
            radius_j <= radius_i
            and objective_j <= objective_i
            and (radius_j < radius_i or objective_j < objective_i)
            for j, (radius_j, objective_j) in enumerate(points)
            if j != i
        )
        flags.append(not dominated)
    return flags


def current_districting_row(
    bridges_csv: Path,
    index_of: dict[str, int],
    distance_matrix: np.ndarray,
    bundle_limit: int,
    repair_probability: float,
) -> tuple[dict[str, object], float]:
    """The current administrative districting: bridges grouped by managing municipality.

    Same objective as ``plot_dm_sensitivity.current_management_baseline``, with the
    realized diameters added so this row can be plotted alongside the optimized ones.
    """
    bridges = pd.read_csv(bridges_csv)
    groups = bridges.assign(_sid=bridges["shisetsu_id"].astype(str)).groupby("管理者")["_sid"]
    diameters, counts = [], []
    for _, members in groups:
        rows = np.array([index_of[sid] for sid in members])
        diameters.append(diameter(rows, distance_matrix))
        counts.append(len(rows))
    objective = sum(
        expected_contracts(count, bundle_limit, repair_probability) for count in counts
    )
    order = np.argsort(counts)[::-1]
    row = {
        "Districting": "current",
        "MaxDistance": "",  # no distance limit is imposed on the current districting
        "M": len(counts),
        "BundleLimit": bundle_limit,
        "ObjectiveValue_Exact": f"{objective:.12f}",
        "RealizedRadius": f"{max(diameters):.6f}",
        "Slack_D_minus_R": "",
        "Reduction(%)": "0.000000",
        "ElapsedSeconds": "",
        "Nondominated": "",
        "RegionDiameters": ";".join(f"{diameters[i]:.3f}" for i in order),
        "RegionCounts": ";".join(str(counts[i]) for i in order),
    }
    # 目的値は書式化した文字列からではなく float のまま返す。削減率の分母なので、
    # 12桁に丸めた値を読み直すと最適化結果との比較でわずかに桁が落ちる。
    return row, objective


def main() -> None:
    args = parse_args()

    index_of, distance_matrix = load_distance_matrix(args.distance_matrix)
    with args.solutions.open("rb") as f:
        solutions = pickle.load(f)
    _, repair_probability = repair_probability_from_transition_matrix(
        DEFAULT_TRANSITION_MATRIX
    )

    current, baseline = current_districting_row(
        args.bridges, index_of, distance_matrix, args.bundle_limit, repair_probability
    )
    print(f"q = {repair_probability!r}")
    print(f"current-management baseline (L={args.bundle_limit}) = {baseline!r}")

    records: list[dict[str, object]] = []
    mismatches: list[tuple[float, int]] = []
    violations: list[str] = []
    for (distance_limit, num_regions), entry in sorted(solutions.items()):
        assignment = np.asarray(entry["assignment"])
        rows = np.array([index_of[str(name)] for name in entry["order"]])
        diameters = [
            diameter(rows[assignment[:, area] == 1], distance_matrix)
            for area in range(assignment.shape[1])
        ]
        counts = sorted(
            (int(assignment[:, area].sum()) for area in range(assignment.shape[1])),
            reverse=True,
        )
        objective = sum(
            expected_contracts(count, args.bundle_limit, repair_probability)
            for count in counts
        )

        stored = entry["row"]
        stored_counts = sorted(
            (int(value) for value in str(stored["RegionCounts"]).split(";") if value),
            reverse=True,
        )
        stored_objective = float(stored["ObjectiveValue_Exact"])
        if counts != stored_counts or abs(objective - stored_objective) > 1e-6:
            mismatches.append((distance_limit, num_regions))

        realized = max(diameters)
        if realized > distance_limit + 1e-6:
            violations.append(
                f"D={distance_limit}, M={num_regions}: R(x*)={realized:.3f} > D"
            )

        records.append(
            {
                "Districting": "optimized",
                "MaxDistance": distance_limit,
                "M": num_regions,
                "BundleLimit": args.bundle_limit,
                "ObjectiveValue_Exact": f"{stored_objective:.12f}",
                "RealizedRadius": f"{realized:.6f}",
                "Slack_D_minus_R": f"{distance_limit - realized:.6f}",
                "Reduction(%)": f"{100 * (1 - stored_objective / baseline):.6f}",
                "ElapsedSeconds": stored.get("ElapsedSeconds", ""),
                "RegionDiameters": ";".join(
                    f"{value:.3f}" for value in sorted(diameters, reverse=True)
                ),
                "RegionCounts": ";".join(str(value) for value in counts),
            }
        )

    print(f"\n検証1 保存行との一致 : {len(records) - len(mismatches)}/{len(records)} ケース")
    print(f"検証2 R(x*) <= D     : {len(records) - len(violations)}/{len(records)} ケース")
    for message in violations:
        print(f"  ✗ {message}")
    if (mismatches or violations) and not args.no_verify:
        raise SystemExit(
            "検証失敗: 上の不一致・制約違反を確認すること（--no-verify で無視可）。"
        )

    flags = nondominated(
        [
            (float(record["RealizedRadius"]), float(record["ObjectiveValue_Exact"]))
            for record in records
        ]
    )
    for record, flag in zip(records, flags):
        record["Nondominated"] = int(flag)

    # 現行区割りは最適化の候補ではなく比較の基準なので、非劣判定には入れず末尾に置く。
    records.append(current)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n非劣解 (Z(x*), R(x*)):")
    print(f"{'D':>6} {'M':>3} {'Z*':>9} {'R(x*)':>8} {'削減率(%)':>10} {'求解(s)':>10}")
    for record in records:
        if record["Nondominated"] == 1:
            print(
                f"{record['MaxDistance']:>6} {record['M']:>3} "
                f"{float(record['ObjectiveValue_Exact']):>9.4f} "
                f"{float(record['RealizedRadius']):>8.2f} "
                f"{float(record['Reduction(%)']):>10.1f} "
                f"{float(record['ElapsedSeconds']):>10.1f}"
            )
    print(f"\n{len(records)} 行を書き出し: {args.output}")


if __name__ == "__main__":
    main()
