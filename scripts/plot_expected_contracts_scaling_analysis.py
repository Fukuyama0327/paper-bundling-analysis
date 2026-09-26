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

出力はパネルごとに分かれる。

* ``expected_contracts_scaling_analysis.pdf``   (a)(b) を横に並べた2枚組
* ``expected_contracts_scaling_analysis_a.pdf`` (a) 単独
* ``expected_contracts_scaling_analysis_b.pdf`` (b) 単独
* ``expected_contracts_saturation.pdf``         (c) 単独

本文はこのうち必要なものをそのまま ``\includegraphics`` で読む。
以前は3枚組から ``viewport`` で切り出していたが、切り出し座標が図の実寸に依存し、
ラベルを変えるだけでパネルがずれるため、2つのファイルに分けた（2026-09-06）。
3枚を1枚にまとめたい場合は ``--with-saturation-panel`` を渡す。

図中にはタイトルもパネル記号も入れない（説明はTeXのキャプションに書く）。
本文のキャプションが言う (a)(b) は、2枚組の並び順（左・右）で対応する。

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

from bundling_analysis.plotting_utils import figure_size, setup_figure_defaults  # noqa: E402

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


def saturation_rate(reduction: float, bundle_limit: int) -> float:
    """Share of the theoretical ceiling ``1 - 1/L`` that a district of size N attains.

    ``eta(N,L) = rho(N,L) / (1 - 1/L)`` answers "how much of what bundling could
    ever deliver at this L has been reached", which is what makes district sizes
    comparable across different L.
    """
    ceiling = 1.0 - 1.0 / bundle_limit
    return float("nan") if ceiling <= 0 else reduction / ceiling


def build_table(
    n_values: list[int], bundle_limits: list[int], q: float
) -> tuple[pd.DataFrame, dict[int, list[float]], dict[int, list[float]], list[float]]:
    """Compute every series once; the figures and the CSVs share these numbers."""
    prob = [probability_two_or_more(n, q) for n in n_values]
    contracts: dict[int, list[float]] = {}
    reduction: dict[int, list[float]] = {}
    saturation: dict[int, list[float]] = {}
    for limit in bundle_limits:
        print(f"  computing f(N, L={limit}) for N = 1..{n_values[-1]} ...", flush=True)
        values = [expected_contracts(n, limit, q) for n in n_values]
        contracts[limit] = values
        reduction[limit] = [1.0 - v / (n * q) for n, v in zip(n_values, values)]
        saturation[limit] = [saturation_rate(r, limit) for r in reduction[limit]]

    table = pd.DataFrame({"N": n_values, "probability_two_or_more_demands": prob})
    for limit in bundle_limits:
        table[f"expected_contracts_L{limit}"] = contracts[limit]
        table[f"reduction_rate_L{limit}"] = reduction[limit]
        table[f"saturation_rate_L{limit}"] = saturation[limit]
    return table, reduction, saturation, prob


def threshold_table(
    n_values: list[int], saturation: dict[int, list[float]], reduction: dict[int, list[float]],
    thresholds: list[float],
) -> pd.DataFrame:
    """First district size at which each ceiling-attainment level is reached.

    ``eta`` increases with N, so the first crossing is the smallest district that
    attains the level. A level not reached within the computed range is reported
    with an empty N so it cannot be mistaken for a small number.
    """
    rows = []
    for limit, values in saturation.items():
        ceiling = 1.0 - 1.0 / limit
        for level in thresholds:
            index = next((i for i, v in enumerate(values) if v >= level), None)
            rows.append({
                "bundle_limit": limit,
                "theoretical_limit": ceiling,
                "target_saturation": level,
                "N": n_values[index] if index is not None else "",
                "reduction_rate": reduction[limit][index] if index is not None else "",
                "saturation_rate": values[index] if index is not None else "",
                "reached_within_range": index is not None,
            })
    return pd.DataFrame(rows)


#: 軸ラベル。(a)(b) を横に並べる狭いパネルでは、1行のままだと枠から食み出すので
#: 折り返した版を使う。文言は水谷先生の指定どおりで、改行位置だけが違う。
XLABEL = "Number of bridges in a management area, $N$"
XLABEL_WRAPPED = "Number of bridges in a\nmanagement area, $N$"


def x_label(compact: bool) -> str:
    return XLABEL_WRAPPED if compact else XLABEL


def draw_saturation(ax, n_values, saturation, bundle_limits, n_study, main_limit,
                    thresholds, panel_label: str = "", compact: bool = False) -> None:
    """Draw eta(N,L): how much of the ceiling 1 - 1/L a district of size N attains."""
    max_n = n_values[-1]
    for level in thresholds:
        ax.axhline(level, color="#d1d5db", linestyle="-", linewidth=0.8, zorder=1)
        ax.annotate(f"{level:.0%}", xy=(max_n, level), xytext=(-2, 3),
                    textcoords="offset points", ha="right", fontsize=7.5, color="#6b7280")
    for index, limit in enumerate(bundle_limits):
        ax.plot(n_values, saturation[limit], linewidth=2.0,
                color=color_for_limit(limit, index), label=rf"$L={limit}$", zorder=2)
    if n_study <= max_n:
        ax.axvline(n_study, color="#6b7280", linestyle=(0, (5, 3)), linewidth=1.2)
    if main_limit in saturation and n_study <= max_n:
        value = saturation[main_limit][n_values.index(n_study)]
        ax.plot([n_study], [value], marker="o", markersize=6, color="#1f2937", zorder=3)
        ax.annotate(f"$N={n_study}$, $L={main_limit}$: {value:.1%}",
                    xy=(n_study, value), xytext=(10, -20), textcoords="offset points",
                    color="#1f2937")
    ax.set_xlabel(x_label(compact))
    ax.set_ylabel(r"Share of theoretical upper bound attained, $\eta$")
    # 図中には見出しもパネル記号も置かない（説明はTeXのキャプションに書く）。
    # 本文のキャプションが言う (a)(b) は、並び順（左・右）で対応させる。
    ax.set_xlim(0, max_n)
    ax.set_ylim(0, 1.02)
    ax.grid(axis="x", color="#d1d5db", linewidth=0.7)
    ax.legend(frameon=False, loc="lower right", ncol=2)


def draw_probability(ax, n_values, prob, q, n_study, highlight_n, compact: bool = False) -> None:
    """(a) 同一年に2件以上の補修需要が発生する確率。"""
    max_n = n_values[-1]
    ax.plot(n_values, prob, linewidth=2.0, color="#4c6fb1")
    if n_study <= max_n:
        ax.axvline(n_study, color="#6b7280", linestyle=(0, (5, 3)), linewidth=1.2)
    for n in [n for n in sorted({*highlight_n, n_study}) if 1 <= n <= max_n]:
        value = probability_two_or_more(n, q)
        ax.plot([n], [value], marker="o", markersize=5, color="#1f2937", zorder=3)
        ax.annotate(f"$N={n}$: {value:.3f}", xy=(n, value),
                    xytext=(6, -12 if n == n_study else 6), textcoords="offset points",
                    color="#1f2937")
    ax.set_xlabel(x_label(compact))
    # 1行だとラベルの長さが枠の高さを決めてしまい、パネルを正方形に近づけられない。
    # 文言は変えず、狭いパネルのときだけ2行に折り返す。
    ax.set_ylabel("Probability of two or more\n" r"repair demands, $\Pr(X \geq 2)$"
                  if compact else
                  r"Probability of two or more repair demands, $\Pr(X \geq 2)$")
    ax.set_xlim(0, max_n)
    ax.set_ylim(0, 1.02)
    ax.grid(color="#d1d5db", linewidth=0.7)


def draw_reduction(ax, n_values, reduction, bundle_limits, n_study, main_limit,
                   compact: bool = False) -> None:
    """(b) 個別発注を基準とした期待契約件数の低減率。"""
    max_n = n_values[-1]
    for index, limit in enumerate(bundle_limits):
        color = color_for_limit(limit, index)
        ax.plot(n_values, reduction[limit], linewidth=2.0, color=color, label=rf"$L={limit}$")
        ax.axhline(1.0 - 1.0 / limit, color=color, linestyle=(0, (1.5, 1.5)),
                   linewidth=1.2)
    if n_study <= max_n:
        ax.axvline(n_study, color="#6b7280", linestyle=(0, (5, 3)), linewidth=1.2)
    if main_limit in reduction and n_study <= max_n:
        value = reduction[main_limit][n_values.index(n_study)]
        ax.plot([n_study], [value], marker="o", markersize=6, color="#1f2937", zorder=3)
        ax.annotate(f"$N={n_study}$, $L={main_limit}$: {value:.3f}", xy=(n_study, value),
                    xytext=(10, -26), textcoords="offset points", color="#1f2937")
    ax.plot([], [], color="#6b7280", linestyle=(0, (1.5, 1.5)), linewidth=1.2,
            label=r"$1 - 1/L$ (upper bound)")
    ax.set_xlabel(x_label(compact))
    ax.set_ylabel(r"Reduction rate, $\rho$")
    ax.set_xlim(0, max_n)
    # (a) と同じ上限にする。片方だけ 1.0 で切ると、並べたとき (a) の上だけ
    # 余白があるように見える（査読コメント 2026-09-25）。
    ax.set_ylim(0, 1.02)
    ax.grid(color="#d1d5db", linewidth=0.7)
    # 2列にすると凡例が軸の幅を超え、目盛ラベルの上へはみ出す（2026-09-27）。
    ax.legend(frameon=False, loc="lower right", ncol=1, labelspacing=0.35)


def plot(
    n_values: list[int],
    prob: list[float],
    reduction: dict[int, list[float]],
    saturation: dict[int, list[float]],
    bundle_limits: list[int],
    q: float,
    n_study: int,
    main_limit: int,
    highlight_n: list[int],
    output_stem: Path,
    thresholds: list[float],
    with_saturation_panel: bool = True,
) -> list[Path]:
    if with_saturation_panel:
        fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=figure_size(1.0, aspect=0.30))
    else:
        # (a) の y 軸ラベル「Probability of two or more repair demands, ...」は長いので、
        # パネルを低くすると端が切れる。縦は余裕をもって取る。
        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=figure_size(1.0, aspect=0.50))
        ax_c = None
    draw_probability(ax_a, n_values, prob, q, n_study, highlight_n, compact=True)
    draw_reduction(ax_b, n_values, reduction, bundle_limits, n_study, main_limit,
                   compact=True)

    # --- Panel (c): share of the theoretical ceiling that is attained ---------
    if ax_c is not None:
        draw_saturation(ax_c, n_values, saturation, bundle_limits, n_study, main_limit,
                        thresholds)

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
    parser.add_argument(
        "--thresholds-output",
        type=Path,
        default=Path("outputs/expected_contracts_scaling_thresholds.csv"),
        help="District size at which each ceiling-attainment level is first reached.",
    )
    parser.add_argument(
        "--saturation-thresholds", type=float, nargs="+",
        default=[0.50, 0.75, 0.80, 0.90, 0.95],
        help="Ceiling-attainment levels to report.",
    )
    parser.add_argument(
        "--panel-width-fraction",
        type=float,
        default=0.49,
        help=(
            "(a)(b) の単独版を作るときの、本文幅に対する配置幅の割合。本文側が "
            "subfigure を width=0.49\\linewidth で置くなら 0.48 を渡す。図をこの実寸で "
            "作ることで、配置時の倍率が 1.0 になり文字の大きさが他の図と揃う。"
        ),
    )
    parser.add_argument(
        "--saturation-stem",
        type=Path,
        default=Path("figures/expected_contracts_saturation"),
        help="Stand-alone version of panel (c). Pass an empty string to skip it.",
    )
    parser.add_argument(
        "--with-saturation-panel", action="store_true",
        help="Append panel (c) to the main figure. 既定では出力しない: 本文は (a)(b) の"
             " 2枚組をFigure 4、(c) の単独図をFigure 5として別々に読むため。",
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
    table, reduction, saturation, prob = build_table(n_values, args.bundle_limits, q)

    table.insert(0, "repair_probability_q", q)
    table.insert(1, "transition_matrix_name", matrix_name)
    table.insert(2, "transition_matrix_sha256_12", matrix_digest)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.csv_output, index=False)
    print(f"Wrote {args.csv_output}")

    thresholds = sorted(args.saturation_thresholds)
    thresholds_table = threshold_table(n_values, saturation, reduction, thresholds)
    args.thresholds_output.parent.mkdir(parents=True, exist_ok=True)
    thresholds_table.to_csv(args.thresholds_output, index=False)
    print(f"Wrote {args.thresholds_output}")

    for path in plot(n_values, prob, reduction, saturation, args.bundle_limits, q,
                     n_study, main_limit, args.highlight_n, args.output_stem, thresholds,
                     with_saturation_panel=args.with_saturation_panel):
        print(f"Wrote {path}")

    # パネル単体のファイル。本文のレイアウトを組みやすいよう、(a)(b) を1枚ずつでも出す。
    # 座標指定で切り出す必要がないので、図の寸法が変わっても本文は壊れない。
    for name, drawer in [
        ("a", lambda ax: draw_probability(ax, n_values, prob, q, n_study, args.highlight_n,
                                          compact=True)),
        ("b", lambda ax: draw_reduction(ax, n_values, reduction, args.bundle_limits,
                                        n_study, main_limit, compact=True)),
    ]:
        # 本文が (a)(b) を subfigure として横に並べる場合に等倍で収まる寸法。
        # 2枚組PDFを viewport で切り出す方式は、図の実寸を変えるたびに座標がずれる
        # （実際 2026-09-27 に (a)(b) の文字が切断された）。単独版を使えば起きない。
        fig, ax = plt.subplots(
            figsize=figure_size(args.panel_width_fraction, aspect=0.98))
        drawer(ax)
        fig.tight_layout()
        stem = args.output_stem.with_name(f"{args.output_stem.name}_{name}")
        for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
            path = stem.with_suffix(f".{ext}")
            fig.savefig(path, bbox_inches="tight", **kwargs)
            print(f"Wrote {path}")
        plt.close(fig)

    # 独立版の (c)。3枚並べると各パネルが細くなるため、単独でも使えるようにしておく。
    if str(args.saturation_stem):
        fig, ax = plt.subplots(figsize=figure_size(0.78, aspect=0.66))
        draw_saturation(ax, n_values, saturation, args.bundle_limits, n_study, main_limit,
                        thresholds, panel_label="")   # 図中タイトルなし
        pass  # 単独図は説明をTeXのキャプションに任せる（図中タイトルなし）
        fig.tight_layout()
        args.saturation_stem.parent.mkdir(parents=True, exist_ok=True)
        for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
            path = args.saturation_stem.with_suffix(f".{ext}")
            fig.savefig(path, bbox_inches="tight", **kwargs)
            print(f"Wrote {path}")
        plt.close(fig)

    print("\n--- key values ---")
    for n in sorted({*args.highlight_n, n_study}):
        print(f"P(X>=2 | N={n}) = {probability_two_or_more(n, q):.6f}")
    for limit in args.bundle_limits:
        f_study = expected_contracts(n_study, limit, q)
        rho = 1.0 - f_study / (n_study * q)
        print(f"N={n_study}, L={limit}: f = {f_study:.6f}, "
              f"reduction = {rho:.6f} (ceiling {1.0 - 1.0 / limit:.6f}, "
              f"saturation = {saturation_rate(rho, limit):.4f})")
    print(f"individual ordering at N={n_study}: N*q = {n_study * q:.6f}")

    print("\n--- district size needed to attain each share of the ceiling ---")
    pivot = thresholds_table.pivot(index="bundle_limit", columns="target_saturation", values="N")
    print(pivot.to_string())


if __name__ == "__main__":
    main()
