"""Re-evaluate optimization result rows with the exact closed-form objective."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from bundling_analysis.expected_contracts import (
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-evaluate Gurobi region counts with exact f(N, L)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/optimization_results_closed_form_20251207_200558.csv"),
        help="Optimization result CSV with Region_*_Count columns.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/optimization_results_exact_objective.csv"),
        help="Output CSV path.",
    )
    parser.add_argument("--bundle-limit", type=int, default=5, help="Bundle limit L.")
    return parser.parse_args()


def parse_region_counts(row: dict[str, str]) -> list[int]:
    counts: list[int] = []
    for index in range(1, 20):
        value = row.get(f"Region_{index}_Count")
        if value in (None, ""):
            continue
        counts.append(int(float(value)))
    return counts


def main() -> None:
    args = parse_args()
    _, repair_probability = repair_probability_from_transition_matrix(
        DEFAULT_TRANSITION_MATRIX
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    fieldnames = [
        "MaxDistance",
        "M",
        "ObjectiveValue_PWL",
        "ObjectiveValue_Exact",
        "Difference_PWL_minus_Exact",
        "RegionCounts",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            counts = parse_region_counts(row)
            exact = sum(
                expected_contracts(count, args.bundle_limit, repair_probability)
                for count in counts
            )
            pwl = float(row["ObjectiveValue"])
            writer.writerow(
                {
                    "MaxDistance": row["MaxDistance"],
                    "M": row["M"],
                    "ObjectiveValue_PWL": f"{pwl:.12f}",
                    "ObjectiveValue_Exact": f"{exact:.12f}",
                    "Difference_PWL_minus_Exact": f"{pwl - exact:.12f}",
                    "RegionCounts": ";".join(str(count) for count in counts),
                }
            )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
