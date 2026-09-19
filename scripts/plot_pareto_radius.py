"""Plot the tradeoff between realized within-area distance R(x*) and contracts Z(x*).

Companion to ``figures/dm_sensitivity`` (FIG. 6 in the manuscript), which puts the
*imposed* limit D on the horizontal axis. Here the horizontal axis is the *realized*
maximum within-area distance R(x*), so the plot shows the tradeoff the districting
actually achieves rather than the constraint it was given.

Markers are coded by the number of management areas M in both colour and shape:
R(x*) lands on almost the same value for every M at a given D, so points would be
indistinguishable if only the colour differed. Nondominated points are filled and
drawn last so they are never hidden behind a dominated point sitting on top of them;
dominated points are drawn as open markers.

"Nondominated" here means nondominated **among the 36 computed solutions** — the
feasible (D, M) combinations solved at a single bundling limit L = 5. It is not a
statement about the continuous Pareto frontier of the underlying problem: Eq. (18)
does not minimize R(x) among assignments attaining the optimal objective value, so
a solution with the same Z(x*) and a smaller R(x*) may well exist without appearing
in this set.

Input is the table written by ``compute_realized_radius.py``; no re-optimization is
involved.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.plotting_utils import (  # noqa: E402
    M_COLORS,
    M_MARKER_SIZE_SCALE,
    M_MARKERS,
    setup_figure_defaults,
)

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
setup_figure_defaults()

BASE_MARKER_SIZE = 44
#: 劣解は一回り小さく描く。同じ D の劣解どうしは Z が 0.01 程度しか違わず必ず重なるので、
#: 小さめの白抜きにしておくと、輪郭が少しずつずれて「複数点がある」ことが読み取れる。
DOMINATED_SIZE_RATIO = 0.72


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/realized_radius.csv"),
        help="Table written by compute_realized_radius.py.",
    )
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=Path("figures/pareto_radius"),
        help="Output path without extension; .png/.svg/.pdf are all written.",
    )
    parser.add_argument(
        "--annotate-d",
        action="store_true",
        help="Label each nondominated point with the distance limit D that produced it.",
    )
    return parser.parse_args()


def marker_size(num_regions: int) -> float:
    return BASE_MARKER_SIZE * M_MARKER_SIZE_SCALE.get(int(num_regions), 1.0)


def main() -> None:
    args = parse_args()
    table = pd.read_csv(args.input)

    optimized = table[table["Districting"] == "optimized"].copy()
    current = table[table["Districting"] == "current"]
    if optimized.empty:
        raise SystemExit(f"{args.input} に optimized 行がありません。")

    fig, ax = plt.subplots(figsize=(7.4, 5.0))

    # 非劣解を結ぶ階段線。パレートフロンティアは点の集合であって曲線ではないので、
    # 点と点の間を直線で結ばず、達成可能な領域の境界として階段で描く。
    frontier = optimized[optimized["Nondominated"] == 1].sort_values("RealizedRadius")
    ax.step(
        frontier["RealizedRadius"],
        frontier["ObjectiveValue_Exact"],
        where="post",
        color="#9ca3af",
        linewidth=1.4,
        zorder=1,
        label="Nondominated frontier",
    )

    # 劣解を先に、非劣解を後に描く。R(x*) は D ごとにほぼ同じ値へ張り付くため、
    # 描画順を決めておかないと非劣解が他の点の下へ潜り込む。
    print("Plotted points (R(x*), Z(x*)) by M:")
    for num_regions in sorted(optimized["M"].unique()):
        subset = optimized[optimized["M"] == num_regions].sort_values("RealizedRadius")
        dominated = subset[subset["Nondominated"] != 1]
        ax.scatter(
            dominated["RealizedRadius"],
            dominated["ObjectiveValue_Exact"],
            s=marker_size(num_regions) * DOMINATED_SIZE_RATIO,
            marker=M_MARKERS.get(int(num_regions), "o"),
            facecolor="none",
            edgecolor=M_COLORS.get(int(num_regions)),
            linewidth=1.0,
            zorder=2,
        )
        for _, row in subset.iterrows():
            marker = " *" if row["Nondominated"] == 1 else "  "
            print(
                f"  M={int(num_regions)}, D={row['MaxDistance']:>4}: "
                f"R={row['RealizedRadius']:7.3f}, Z={row['ObjectiveValue_Exact']:.6f}{marker}"
            )

    for num_regions in sorted(frontier["M"].unique()):
        subset = frontier[frontier["M"] == num_regions]
        ax.scatter(
            subset["RealizedRadius"],
            subset["ObjectiveValue_Exact"],
            s=marker_size(num_regions) * 1.35,
            marker=M_MARKERS.get(int(num_regions), "o"),
            color=M_COLORS.get(int(num_regions)),
            edgecolor="#111827",
            linewidth=0.9,
            zorder=5,
        )

    if args.annotate_d:
        # D>=40 では距離制約が対象322橋の直径に達し、複数の D が同一の解になる。
        # 同じ D でも M 違いで R が数十mだけずれることがある（Eq.(18)は最適値を
        # 与える割当の中で R を最小化しないため）。1km に丸めて同じ位置とみなす。
        rightmost = frontier["RealizedRadius"].max()
        for _, group in frontier.groupby(frontier["RealizedRadius"].round(0)):
            limits = sorted(group["MaxDistance"].unique())
            if len(limits) == 1:
                label = f"$D={limits[0]:.0f}$"
            else:
                label = f"$D={limits[0]:.0f}$–${limits[-1]:.0f}$"
            radius = group["RealizedRadius"].max()
            # 右端の点だけはラベルを左側に出す（右に置くと軸の外へ出る）。
            at_right_edge = radius >= rightmost - 1e-9
            ax.annotate(
                label,
                (radius, group["ObjectiveValue_Exact"].min()),
                textcoords="offset points",
                xytext=(-7, -14) if at_right_edge else (7, -12),
                ha="right" if at_right_edge else "left",
                fontsize=8,
                color="#4b5563",
            )

    if not current.empty:
        row = current.iloc[0]
        ax.scatter(
            [row["RealizedRadius"]],
            [row["ObjectiveValue_Exact"]],
            marker="*",
            s=230,
            color="#111827",
            zorder=6,
        )
        print(
            f"\nCurrent administrative districting: "
            f"R={row['RealizedRadius']:.3f}, Z={row['ObjectiveValue_Exact']:.6f}"
        )

    ax.set_xlabel("Realized maximum within-area distance, $R(x^*)$ (km)")
    ax.set_ylabel("Expected annual number of contracts, $Z(x^*)$")
    # ラベルが右端で切れないよう横方向に余白を足す。
    ax.margins(x=0.07)
    ax.grid(color="#d1d5db", linewidth=0.7)

    # 凡例は手で組む。M の色と形の対応、塗りの有無が何を意味するか、
    # 現行区割りの記号までを1か所で読めるようにするため。
    handles = [
        Line2D([], [], color="#9ca3af", linewidth=1.4, label="Nondominated frontier")
    ]
    for num_regions in sorted(optimized["M"].unique()):
        handles.append(
            Line2D(
                [], [], linestyle="none",
                marker=M_MARKERS.get(int(num_regions), "o"),
                markerfacecolor="none",
                markeredgecolor=M_COLORS.get(int(num_regions)),
                markeredgewidth=1.0, markersize=6.5,
                label=f"$M = {int(num_regions)}$",
            )
        )
    handles.append(
        Line2D(
            # M のどれかと取り違えられないよう、凡例の塗りは配色に無い中間色にする。
            [], [], linestyle="none", marker="o", markerfacecolor="#d1d5db",
            markeredgecolor="#111827", markeredgewidth=0.9, markersize=8,
            label="Nondominated among the 36 computed solutions",
        )
    )
    if not current.empty:
        handles.append(
            Line2D(
                [], [], linestyle="none", marker="*", color="#111827", markersize=14,
                label="Current administrative districting",
            )
        )
    # データは左上（小さい R・多い Z）から右下へ下がるので、左下は必ず空く
    # （R が小さく Z も小さい領域は実行不可能）。
    ax.legend(handles=handles, frameon=False, ncol=2, fontsize=8.5, loc="lower left")

    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for extension, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{extension}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
