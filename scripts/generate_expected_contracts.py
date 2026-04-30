"""Generate closed-form expected contract counts for Figure 2 candidates."""

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
        description="Generate expected contract counts f(N, L) from the closed-form model."
    )
    parser.add_argument("--max-n", type=int, default=323, help="Maximum number of bridges.")
    parser.add_argument(
        "--bundle-limits",
        type=int,
        nargs="+",
        default=[1, 3, 5, 7, 10],
        help="Bundle limits L to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/expected_contracts_closed_form.csv"),
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_n < 1:
        raise ValueError("--max-n must be positive")

    _, repair_probability = repair_probability_from_transition_matrix(
        DEFAULT_TRANSITION_MATRIX
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["N", "L", "repair_probability", "expected_contracts"],
        )
        writer.writeheader()
        for bundle_limit in args.bundle_limits:
            for num_bridges in range(1, args.max_n + 1):
                expected_count = expected_contracts(
                    num_bridges,
                    bundle_limit,
                    repair_probability,
                )
                writer.writerow(
                    {
                        "N": num_bridges,
                        "L": bundle_limit,
                        "repair_probability": f"{repair_probability:.12f}",
                        "expected_contracts": f"{expected_count:.12f}",
                    }
                )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
