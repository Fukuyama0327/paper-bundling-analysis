"""Re-evaluate optimization result rows with the exact closed-form objective.

Reads a Gurobi result CSV that carries ``Region_*_Count`` columns and rewrites
each row's objective as the exact closed form ``sum f(N_m, L)`` instead of the
PWL approximation used inside the solver.

``--input`` and ``--output`` are both required on purpose. Until 2026-08-13 they
defaulted to ``optimization_results_closed_form_20251207_200558.csv`` and
``optimization_results_exact_objective.csv`` respectively, so running the script
with no arguments silently rewrote the canonical result file from a superseded
solver run. That combination is wrong twice over:

* The canonical file is **not** produced by this script. It is the direct output
  of the all-integer-PWL full-grid run of ``run_gurobi_districting.py``
  (commit a3a2f61), whose assignments live in
  ``data/processed/districting_solutions_all36.pkl``. The 20251207_200558 series
  is an earlier run that reaches a worse objective in 11 of the 36 cases.
* This script writes fewer columns than the solver does. ``Status``,
  ``ElapsedSeconds`` and ``PWLNodes`` would be dropped, breaking
  ``plot_dm_sensitivity.py`` (filters on ``Status``) and
  ``plot_expected_contracts_scaling_analysis.py`` (reads ``BundleLimit``).

Overwriting a file that has columns this script does not write now requires
``--force``.

Usage:
    python scripts/reevaluate_optimization_objectives.py \
        --input outputs/new_gurobi_results.csv \
        --output outputs/new_gurobi_results_exact.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

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
        required=True,
        help="Optimization result CSV with Region_*_Count columns.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help=(
            "Output CSV path. Required: there is deliberately no default, because "
            "the previous default pointed at the canonical result file."
        ),
    )
    parser.add_argument("--bundle-limit", type=int, default=5, help="Bundle limit L.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output even if it carries columns this script does not write.",
    )
    return parser.parse_args()


def parse_region_counts(row: dict[str, str]) -> list[int]:
    counts: list[int] = []
    for index in range(1, 20):
        value = row.get(f"Region_{index}_Count")
        if value in (None, ""):
            continue
        counts.append(int(float(value)))
    return counts


FIELDNAMES = [
    "MaxDistance",
    "M",
    "ObjectiveValue_PWL",
    "ObjectiveValue_Exact",
    "Difference_PWL_minus_Exact",
    "RegionCounts",
    "BundleLimit",
]


def check_output_target(output: Path, force: bool) -> None:
    """Refuse to silently drop columns the target file already carries."""
    if force or not output.exists():
        return
    with output.open(encoding="utf-8-sig", newline="") as f:
        existing = next(csv.reader(f), [])
    dropped = [name for name in existing if name not in FIELDNAMES]
    if dropped:
        raise SystemExit(
            f"{output} already has columns this script does not write: {dropped}.\n"
            "It looks like a run_gurobi_districting.py output (the canonical result "
            "file is one). Overwriting it would drop those columns and break "
            "plot_dm_sensitivity.py / plot_expected_contracts_scaling_analysis.py.\n"
            "Write somewhere else, or pass --force if you really mean it."
        )


def main() -> None:
    args = parse_args()
    _, repair_probability = repair_probability_from_transition_matrix(
        DEFAULT_TRANSITION_MATRIX
    )
    check_output_target(args.output, args.force)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    fieldnames = FIELDNAMES
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
                    "BundleLimit": args.bundle_limit,
                }
            )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
