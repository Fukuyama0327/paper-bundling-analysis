"""Record the realized maximum within-area distance R(x*) for each optimized solution.

The manuscript reports only the imposed distance limit ``D``. A reviewer asked for
the *realized* maximum within-area distance ``R(x*) = max_k R_k(x*)`` as well, so
that varying ``D`` traces the nondominated relationship between ``Z(x*)`` and
``R(x*)`` directly, without the unit-dependent weight alpha of Eq. (17).

Nothing has to be re-solved for this: ``run_gurobi_districting.py`` already stores
the assignment matrix of every case, so ``R_k`` is a lookup in the distance matrix.

Note that Eq. (18) does not minimize ``R(x)`` among assignments sharing the optimal
objective value, so ``R(x*)`` is what the solver happened to return, not the
smallest realized distance attaining ``Z(x*)``. Expect ``R(x*)`` to sit just under
``D`` in most cases.

Usage:
    python scripts/compute_realized_radius.py \
        --output outputs/realized_radius.csv
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute realized max within-area distance R(x*) per optimized case."
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
            "Target bridge CSV, used only to recompute the current-administrative "
            "baseline for the Reduction(%%) column. The baseline depends on L, so it "
            "cannot be hard-coded once a bundle limit other than 5 is analysed."
        ),
    )
    parser.add_argument(
        "--baseline-objective",
        type=float,
        default=None,
        help="Override the baseline instead of recomputing it from --bridges.",
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


def current_management_baseline(bridges_csv: Path, bundle_limit: int, q: float) -> float:
    """Recompute the current-management objective from per-municipality counts.

    Same computation as ``plot_dm_sensitivity.current_management_baseline``.
    """
    counts = pd.read_csv(bridges_csv)["管理者"].value_counts()
    return sum(expected_contracts(int(count), bundle_limit, q) for count in counts)


def load_distance_matrix(path: Path) -> tuple[dict[str, int], np.ndarray]:
    with path.open("rb") as f:
        data = pickle.load(f)
    order = [str(item) for item in data["order"]]
    matrix = np.asarray(data["d_core"], dtype=float)
    if matrix.shape != (len(order), len(order)):
        raise SystemExit("distance matrix shape does not match order length")
    return {name: index for index, name in enumerate(order)}, matrix


def area_diameters(
    assignment: np.ndarray, rows: np.ndarray, distance_matrix: np.ndarray
) -> list[float]:
    """R_k for every area. A single-bridge (or empty) area has diameter 0."""
    diameters: list[float] = []
    for area in range(assignment.shape[1]):
        members = rows[assignment[:, area] == 1]
        if len(members) > 1:
            diameters.append(float(distance_matrix[np.ix_(members, members)].max()))
        else:
            diameters.append(0.0)
    return diameters


def nondominated(points: list[tuple[float, float]]) -> list[bool]:
    """Minimize both coordinates; a point is dominated if another is <= in both and < in one."""
    flags = []
    for i, (ri, zi) in enumerate(points):
        dominated = any(
            rj <= ri and zj <= zi and (rj < ri or zj < zi)
            for j, (rj, zj) in enumerate(points)
            if j != i
        )
        flags.append(not dominated)
    return flags


def main() -> None:
    args = parse_args()

    index_of, distance_matrix = load_distance_matrix(args.distance_matrix)
    with args.solutions.open("rb") as f:
        solutions = pickle.load(f)
    _, repair_probability = repair_probability_from_transition_matrix(
        DEFAULT_TRANSITION_MATRIX
    )
    baseline = args.baseline_objective
    if baseline is None:
        baseline = current_management_baseline(
            args.bridges, args.bundle_limit, repair_probability
        )
    print(f"current-management baseline (L={args.bundle_limit}) = {baseline!r}")

    records = []
    mismatches = []
    for (distance_limit, num_regions), entry in sorted(solutions.items()):
        assignment = np.asarray(entry["assignment"])
        rows = np.array([index_of[str(name)] for name in entry["order"]])
        diameters = area_diameters(assignment, rows, distance_matrix)
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
            raise SystemExit(
                f"D={distance_limit}, M={num_regions}: R(x*)={realized:.3f} exceeds the "
                "imposed limit; the stored assignment violates its own distance constraint."
            )

        records.append(
            {
                "MaxDistance": distance_limit,
                "M": num_regions,
                "BundleLimit": args.bundle_limit,
                "ObjectiveValue_Exact": f"{stored_objective:.12f}",
                "RealizedRadius": f"{realized:.6f}",
                "Slack_D_minus_R": f"{distance_limit - realized:.6f}",
                "Reduction(%)": f"{100 * (1 - stored_objective / baseline):.6f}",
                "RegionDiameters": ";".join(
                    f"{value:.3f}" for value in sorted(diameters, reverse=True)
                ),
                "RegionCounts": ";".join(str(value) for value in counts),
            }
        )

    if mismatches and not args.no_verify:
        raise SystemExit(
            f"検証失敗: {len(mismatches)} ケースで再計算した件数・目的値が保存行と一致しません "
            f"（例: {mismatches[:3]}）。--no-verify で無視可。"
        )

    points = [
        (float(record["RealizedRadius"]), float(record["ObjectiveValue_Exact"]))
        for record in records
    ]
    for record, flag in zip(records, nondominated(points)):
        record["Nondominated"] = int(flag)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "MaxDistance",
        "M",
        "BundleLimit",
        "ObjectiveValue_Exact",
        "RealizedRadius",
        "Slack_D_minus_R",
        "Reduction(%)",
        "Nondominated",
        "RegionDiameters",
        "RegionCounts",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"検証: {len(records) - len(mismatches)}/{len(records)} ケースが保存行と一致")
    print(f"\n非劣解 (Z(x*), R(x*)):")
    print(f"{'D':>6} {'M':>3} {'Z*':>9} {'R(x*)':>8} {'削減率(%)':>10}")
    for record in records:
        if record["Nondominated"]:
            print(
                f"{record['MaxDistance']:>6} {record['M']:>3} "
                f"{float(record['ObjectiveValue_Exact']):>9.4f} "
                f"{float(record['RealizedRadius']):>8.2f} "
                f"{float(record['Reduction(%)']):>10.1f}"
            )
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
