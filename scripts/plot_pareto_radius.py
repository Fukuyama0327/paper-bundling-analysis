"""Plot the tradeoff between realized within-area distance R(x*) and contracts Z(x*).

Companion to ``figures/dm_sensitivity``, which puts the *imposed* limit D on the
horizontal axis. Here the horizontal axis is the *realized* maximum within-area
distance R(x*), so the plot shows the tradeoff the districting actually achieves
rather than the constraint it was given. Markers are coloured by the number of
management areas M, the nondominated set is joined by a staircase, and the current
administrative districting is drawn as a reference point.

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.plotting_utils import M_COLORS, setup_figure_defaults  # noqa: E402

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
setup_figure_defaults()


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


def main() -> None:
    args = parse_args()
    table = pd.read_csv(args.input)

    optimized = table[table["Districting"] == "optimized"].copy()
    current = table[table["Districting"] == "current"]
    if optimized.empty:
        raise SystemExit(f"{args.input} に optimized 行がありません。")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))

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

    print("Plotted points (R(x*), Z(x*)) by M:")
    for num_regions in sorted(optimized["M"].unique()):
        subset = optimized[optimized["M"] == num_regions].sort_values("RealizedRadius")
        ax.scatter(
            subset["RealizedRadius"],
            subset["ObjectiveValue_Exact"],
            s=40,
            color=M_COLORS.get(int(num_regions)),
            edgecolor="white",
            linewidth=0.6,
            alpha=0.9,
            zorder=3,
            label=f"$M = {int(num_regions)}$",
        )
        for _, row in subset.iterrows():
            marker = " *" if row["Nondominated"] == 1 else "  "
            print(
                f"  M={int(num_regions)}, D={row['MaxDistance']:>4}: "
                f"R={row['RealizedRadius']:7.3f}, Z={row['ObjectiveValue_Exact']:.6f}{marker}"
            )

    if args.annotate_d:
        # D>=40 では距離制約が対象322橋の直径に達し、複数の D が同一の解になる。
        # R が同じ点にラベルを重ね書きしないよう、R ごとに D をまとめて1つだけ置く。
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
                xytext=(-5, -13) if at_right_edge else (5, -11),
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
            s=210,
            color="#111827",
            zorder=4,
            label="Current administrative districting",
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
    # 凡例は左下へ。データは左上（小さい R・多い Z）から右下へ下がるので、
    # 左下は必ず空く（R が小さく Z も小さい領域は実行不可能）。
    ax.legend(frameon=False, ncol=2, fontsize=9, loc="lower left")
    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for extension, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{extension}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
