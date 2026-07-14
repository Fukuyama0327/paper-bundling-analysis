"""Break down the districting objective into per-region contributions.

For each selected (D, M) case this shows how each region -- depending on its size
N_m -- contributes to the total expected number of contracts f = sum_m f(N_m, L).
Region sizes come from the ``RegionCounts`` column of the canonical result grid, so
no per-bridge assignment (solutions pkl) is needed: the objective depends only on
the region sizes. This supports the discussion of the districting maps (cf. the
component analysis in the source notebook, cell 39).
"""

from __future__ import annotations

import argparse
import csv
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


def parse_case(text: str) -> tuple[float, int]:
    d_str, m_str = text.split(":")
    return float(d_str), int(m_str)


def region_counts(df: pd.DataFrame, d: float, m: int) -> list[int]:
    row = df[(df["MaxDistance"] == d) & (df["M"] == m)]
    if row.empty:
        raise SystemExit(f"CSV に D={d}, M={m} の行がありません。")
    counts = [int(x) for x in str(row.iloc[0]["RegionCounts"]).split(";") if x != ""]
    return sorted(counts, reverse=True)


def exact_objective(df: pd.DataFrame, d: float, m: int) -> float:
    row = df[(df["MaxDistance"] == d) & (df["M"] == m)]
    return float(row.iloc[0]["ObjectiveValue_Exact"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/optimization_results_exact_objective.csv"),
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        default=["25:3", "35:3", "40:1"],
        help="Representative D:M cases (default 25:3 35:3 40:1).",
    )
    parser.add_argument("--bundle-limit", type=int, default=5)
    parser.add_argument("--output-stem", type=Path, default=Path("figures/region_breakdown"))
    parser.add_argument("--table-output", type=Path, default=Path("outputs/region_breakdown.csv"))
    args = parser.parse_args()

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    df = pd.read_csv(args.input)
    cases = [parse_case(c) for c in args.cases]

    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    cmap = plt.cm.viridis
    labels = [f"$D={int(d)}$ km,\n$M={m}$" for d, m in cases]
    x = range(len(cases))

    table_rows: list[dict] = []
    all_ok = True
    for xi, (d, m) in zip(x, cases):
        counts = region_counts(df, d, m)
        contribs = [expected_contracts(n, args.bundle_limit, q) for n in counts]
        bottom = 0.0
        for r, (n, fval) in enumerate(zip(counts, contribs)):
            color = cmap(r / max(len(counts) - 1, 1))
            ax.bar(xi, fval, bottom=bottom, width=0.6, color=color, edgecolor="white", linewidth=0.6)
            if fval > 0.04:  # annotate region size only where the segment is readable
                ax.text(xi, bottom + fval / 2, f"$N_m$={n}", ha="center", va="center",
                        fontsize=8, color="white")
            bottom += fval
            table_rows.append({"D": d, "M": m, "region_rank": r + 1, "N_m": n,
                               "f_Nm": f"{fval:.6f}"})
        total = sum(contribs)
        target = exact_objective(df, d, m)
        ok = abs(total - target) < 1e-9
        all_ok = all_ok and ok
        ax.text(xi, bottom + 0.02, f"{total:.3f}", ha="center", va="bottom", fontsize=9)
        print(f"D={d}, M={m}: sum f(N_m)={total:.9f} vs CSV Exact={target:.9f} "
              f"-> {'OK' if ok else 'MISMATCH'}  (N_m={counts})")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Expected annual number of contracts")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#d1d5db", linewidth=0.7)
    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)

    args.table_output.parent.mkdir(parents=True, exist_ok=True)
    with args.table_output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["D", "M", "region_rank", "N_m", "f_Nm"])
        writer.writeheader()
        writer.writerows(table_rows)
    print(f"Wrote {args.table_output}")

    if not all_ok:
        raise SystemExit("検証失敗: 内訳の合計が ObjectiveValue_Exact と一致しません。")


if __name__ == "__main__":
    main()
