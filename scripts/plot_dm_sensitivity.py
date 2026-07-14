"""Plot the D-M sensitivity of the districting objective (all M series per D).

Unlike ``figures/optimization_results.png`` (which shows only the best M at each
distance limit), this figure draws one line per number of regions M so the full
sensitivity to the distance limit D and the region count M is visible. Values are
the exact closed-form objective ``ObjectiveValue_Exact`` from the canonical
all-integer-PWL result grid; infeasible / uncomputed (D, M) combinations are left
as gaps (never interpolated or zero-filled).
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

from bundling_analysis.expected_contracts import (  # noqa: E402
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)

#: Fixed colour per region count M so every figure in the set stays consistent.
M_COLORS = {
    1: "#6b7280",
    2: "#4c6fb1",
    3: "#238b8e",
    4: "#cc6c3b",
    5: "#7a4e9e",
    6: "#b0435b",
}


def current_management_baseline(bridges_csv: Path, bundle_limit: int, q: float) -> float:
    """Recompute the current-management objective from per-municipality counts."""
    df = pd.read_csv(bridges_csv)
    counts = df["管理者"].value_counts()
    return sum(expected_contracts(int(c), bundle_limit, q) for c in counts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/optimization_results_exact_objective.csv"),
    )
    parser.add_argument(
        "--bridges",
        type=Path,
        default=Path("data/processed/target_rc_bridges_322.csv"),
        help="Used only to recompute the current-management baseline.",
    )
    parser.add_argument("--bundle-limit", type=int, default=5)
    parser.add_argument("--output-stem", type=Path, default=Path("figures/dm_sensitivity"))
    args = parser.parse_args()

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    baseline = current_management_baseline(args.bridges, args.bundle_limit, q)
    print(f"q = {q!r}")
    print(f"current-management baseline = {baseline!r}")

    df = pd.read_csv(args.input)
    df = df[df["Status"] == 2]  # keep only solved cases; do not fill gaps

    fig, ax = plt.subplots(figsize=(7.4, 4.8))

    # Baseline (current management) as a labelled horizontal reference line.
    ax.axhline(baseline, color="#333333", linestyle="--", linewidth=1.4,
               label=f"Current management ({baseline:.3f})")

    print("\nPlotted points (D, M, ObjectiveValue_Exact):")
    for m in sorted(df["M"].unique()):
        sub = df[df["M"] == m].sort_values("MaxDistance")
        color = M_COLORS.get(int(m), None)
        ax.plot(sub["MaxDistance"], sub["ObjectiveValue_Exact"],
                marker="o", linewidth=1.8, markersize=5, color=color, label=f"$M = {int(m)}$")
        for _, row in sub.iterrows():
            print(f"  D={row['MaxDistance']:>4}, M={int(m)}: {row['ObjectiveValue_Exact']:.6f}")

    ax.set_xlabel("Distance limit $D$ (km)")
    ax.set_ylabel("Expected annual number of contracts")
    ax.set_xlim(min(df["MaxDistance"]) - 2, max(df["MaxDistance"]) + 2)
    ax.set_ylim(bottom=0)
    ax.grid(color="#d1d5db", linewidth=0.7)
    ax.legend(frameon=False, ncol=2, fontsize=9)
    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
