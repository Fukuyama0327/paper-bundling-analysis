"""Scaling analysis of the closed-form expected contract count (Section 4.3).

Two panels sharing the horizontal axis ``N`` (bridges in one管理エリア):

(a) Probability that two or more repair demands occur in the same year within
    the same district, ``P(X >= 2) = 1 - (1-q)^N - N q (1-q)^(N-1)``. This is the
    event that makes bundling possible at all, so it explains *why* the
    aggregation effect needs a large district.
(b) Reduction rate of the annual expected number of contracts relative to
    individual ordering, ``1 - f(N,L) / (N q)``, with the theoretical ceiling
    ``1 - 1/L`` drawn as a dashed guide.

Nothing is hard-coded: every quantity is derived at run time from the same
sources the rest of the pipeline uses, so re-running the script is enough after
any update.

* ``q``            -- ``repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)``
* ``f(N,L)``       -- ``expected_contracts(N, L, q)`` (no reimplementation)
* study-area ``N`` -- row count of the target-bridge CSV (322 today)
* main-analysis ``L`` -- ``BundleLimit`` column of the canonical optimization
  result CSV (5 today), i.e. the L that actually produced the paper's results;
  ``--main-bundle-limit`` overrides it.

Usage:
    python scripts/plot_expected_contracts_scaling_analysis.py --max-n 1000
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.plotting_utils import setup_figure_defaults  # noqa: E402

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
# 多くの学術誌がType 3を受け付けないため、保存前に必ず適用する。
setup_figure_defaults()

from bundling_analysis import expected_contracts as ec_module  # noqa: E402
from bundling_analysis.expected_contracts import (  # noqa: E402
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)

#: Fixed colour per bundle limit L, shared with plot_expected_contracts_by_limit.py.
L_COLORS = {
    1: "#6b7280",
    3: "#4c6fb1",
    5: "#238b8e",
    7: "#cc6c3b",
    10: "#7a4e9e",
}
FALLBACK_COLORS = ["#b0435b", "#2f6f4f", "#8a6d3b", "#4a4a8a"]


def color_for_limit(limit: int, index: int) -> str:
    return L_COLORS.get(int(limit), FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def transition_matrix_identity(matrix) -> tuple[str, str]:
    """Name the transition matrix in use and fingerprint its values.

    The name is resolved by looking up which module-level constant
    ``DEFAULT_TRANSITION_MATRIX`` currently points at, so re-pointing the
    default (or editing the numbers) changes what the CSV records.
    """
    normalized = tuple(tuple(float(v) for v in row) for row in matrix)
    names = sorted(
        name
        for name in dir(ec_module)
        if name.endswith("TRANSITION_MATRIX")
        and name != "DEFAULT_TRANSITION_MATRIX"
        and isinstance(getattr(ec_module, name), tuple)
        and tuple(tuple(float(v) for v in row) for row in getattr(ec_module, name)) == normalized
    )
    label = "+".join(names) if names else "custom"
    digest = hashlib.sha256(repr(normalized).encode("utf-8")).hexdigest()[:12]
    return label, digest


def study_area_bridge_count(bridges_csv: Path) -> int:
    """Number of target bridges, read from the canonical bridge CSV (never typed in)."""
    return int(len(pd.read_csv(bridges_csv)))


def main_bundle_limit_from_results(results_csv: Path) -> int:
    """Bundle limit L used by the canonical optimization run."""
    df = pd.read_csv(results_csv)
    if "BundleLimit" not in df.columns:
        raise ValueError(f"{results_csv} has no BundleLimit column")
    limits = sorted({int(v) for v in df["BundleLimit"].dropna()})
    if len(limits) != 1:
        raise ValueError(f"{results_csv} mixes several bundle limits: {limits}")
    return limits[0]


def probability_two_or_more(n: int, q: float) -> float:
    """P(X >= 2) for X ~ Binomial(n, q).

    Evaluated as ``1 - (1-q)^(n-1) (1 + (n-1)q)``, which is algebraically the
    same as ``1 - (1-q)^n - n q (1-q)^(n-1)`` but avoids the cancellation that
    makes the literal form return a tiny negative value at n = 1.
    """
    return max(0.0, 1.0 - (1.0 - q) ** (n - 1) * (1.0 + (n - 1) * q))


def build_table(
    n_values: list[int], bundle_limits: list[int], q: float
) -> tuple[pd.DataFrame, dict[int, list[float]], list[float]]:
    """Compute every series once; the figure and the CSV share these numbers."""
    prob = [probability_two_or_more(n, q) for n in n_values]
    contracts: dict[int, list[float]] = {}
    reduction: dict[int, list[float]] = {}
    for limit in bundle_limits:
        print(f"  computing f(N, L={limit}) for N = 1..{n_values[-1]} ...", flush=True)
        values = [expected_contracts(n, limit, q) for n in n_values]
        contracts[limit] = values
        reduction[limit] = [1.0 - v / (n * q) for n, v in zip(n_values, values)]

    table = pd.DataFrame({"N": n_values, "probability_two_or_more_demands": prob})
    for limit in bundle_limits:
        table[f"expected_contracts_L{limit}"] = contracts[limit]
        table[f"reduction_rate_L{limit}"] = reduction[limit]
    return table, reduction, prob


def plot(
    n_values: list[int],
    prob: list[float],
    reduction: dict[int, list[float]],
    bundle_limits: list[int],
    q: float,
    n_study: int,
    main_limit: int,
    highlight_n: list[int],
    output_stem: Path,
) -> list[Path]:
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.6, 4.6))
    max_n = n_values[-1]

    # --- Panel (a): probability of two or more demands in the same year -------
    ax_a.plot(n_values, prob, linewidth=2.0, color="#4c6fb1")
    if n_study <= max_n:
        ax_a.axvline(n_study, color="#9ca3af", linestyle="--", linewidth=1.0)
    marks = [n for n in sorted({*highlight_n, n_study}) if 1 <= n <= max_n]
    for n in marks:
        value = probability_two_or_more(n, q)
        ax_a.plot([n], [value], marker="o", markersize=5, color="#1f2937", zorder=3)
        ax_a.annotate(
            f"$N={n}$: {value:.3f}",
            xy=(n, value),
            xytext=(6, -12 if n == n_study else 6),
            textcoords="offset points",
            fontsize=9,
            color="#1f2937",
        )
    ax_a.set_xlabel("Number of bridges in an area, $N$")
    ax_a.set_ylabel(r"$\Pr(X \geq 2)$")
    ax_a.set_title("(a) Probability of two or more repair demands\nin the same year",
                   fontsize=10)
    ax_a.set_xlim(0, max_n)
    ax_a.set_ylim(0, 1.02)
    ax_a.grid(color="#d1d5db", linewidth=0.7)

    # --- Panel (b): reduction rate against individual ordering ----------------
    for index, limit in enumerate(bundle_limits):
        color = color_for_limit(limit, index)
        ax_b.plot(n_values, reduction[limit], linewidth=2.0, color=color, label=rf"$L={limit}$")
        ax_b.axhline(1.0 - 1.0 / limit, color=color, linestyle=":", linewidth=1.1, alpha=0.8)
    if n_study <= max_n:
        ax_b.axvline(n_study, color="#9ca3af", linestyle="--", linewidth=1.0)
    if main_limit in reduction and n_study <= max_n:
        value = reduction[main_limit][n_values.index(n_study)]
        ax_b.plot([n_study], [value], marker="o", markersize=6, color="#1f2937", zorder=3)
        ax_b.annotate(
            f"$N={n_study}$, $L={main_limit}$: {value:.3f}",
            xy=(n_study, value),
            xytext=(10, -26),
            textcoords="offset points",
            fontsize=9,
            color="#1f2937",
        )
    ax_b.plot([], [], color="#9ca3af", linestyle=":", linewidth=1.1, label=r"$1 - 1/L$ (limit)")
    ax_b.set_xlabel("Number of bridges in an area, $N$")
    ax_b.set_ylabel("Reduction rate vs. individual ordering")
    ax_b.set_title("(b) Reduction rate of the expected annual\nnumber of contracts", fontsize=10)
    ax_b.set_xlim(0, max_n)
    ax_b.set_ylim(0, 1.0)
    ax_b.grid(color="#d1d5db", linewidth=0.7)
    ax_b.legend(frameon=False, loc="lower right", fontsize=9, ncol=2)

    fig.tight_layout()
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        paths.append(path)
    plt.close(fig)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-n", type=int, default=1000)
    parser.add_argument("--bundle-limits", type=int, nargs="+", default=[3, 5, 7, 10])
    parser.add_argument("--highlight-n", type=int, nargs="+", default=[50, 100, 200])
    parser.add_argument(
        "--bridges",
        type=Path,
        default=Path("data/processed/target_rc_bridges_322.csv"),
        help="Target-bridge CSV; its row count gives the study-area N.",
    )
    parser.add_argument(
        "--optimization-results",
        type=Path,
        default=Path("data/processed/optimization_results_exact_objective.csv"),
        help="Canonical result CSV; its BundleLimit column gives the main-analysis L.",
    )
    parser.add_argument(
        "--main-bundle-limit",
        type=int,
        default=None,
        help="Override the main-analysis L instead of reading it from the result CSV.",
    )
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=Path("figures/expected_contracts_scaling_analysis"),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("outputs/expected_contracts_scaling_analysis.csv"),
    )
    args = parser.parse_args()

    if args.max_n < 1:
        parser.error("--max-n must be at least 1")

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    matrix_name, matrix_digest = transition_matrix_identity(DEFAULT_TRANSITION_MATRIX)
    n_study = study_area_bridge_count(args.bridges)
    main_limit = (
        args.main_bundle_limit
        if args.main_bundle_limit is not None
        else main_bundle_limit_from_results(args.optimization_results)
    )

    print(f"q = {q!r}")
    print(f"transition matrix = {matrix_name} (sha256:{matrix_digest})")
    print(f"study-area bridges N = {n_study} (from {args.bridges})")
    print(f"main-analysis L = {main_limit} (from {args.optimization_results})")
    if n_study > args.max_n:
        print(f"warning: study-area N={n_study} exceeds --max-n={args.max_n}; "
              "annotations are omitted from the figure")

    n_values = list(range(1, args.max_n + 1))
    table, reduction, prob = build_table(n_values, args.bundle_limits, q)

    table.insert(0, "repair_probability_q", q)
    table.insert(1, "transition_matrix_name", matrix_name)
    table.insert(2, "transition_matrix_sha256_12", matrix_digest)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.csv_output, index=False)
    print(f"Wrote {args.csv_output}")

    for path in plot(n_values, prob, reduction, args.bundle_limits, q,
                     n_study, main_limit, args.highlight_n, args.output_stem):
        print(f"Wrote {path}")

    print("\n--- key values ---")
    for n in sorted({*args.highlight_n, n_study}):
        print(f"P(X>=2 | N={n}) = {probability_two_or_more(n, q):.6f}")
    for limit in args.bundle_limits:
        f_study = expected_contracts(n_study, limit, q)
        print(f"N={n_study}, L={limit}: f = {f_study:.6f}, "
              f"reduction = {1.0 - f_study / (n_study * q):.6f} "
              f"(ceiling {1.0 - 1.0 / limit:.6f})")
    print(f"individual ordering at N={n_study}: N*q = {n_study * q:.6f}")


if __name__ == "__main__":
    main()
