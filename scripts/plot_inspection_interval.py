# -*- coding: utf-8 -*-
"""fig:inspection_interval の生成: 点検間隔ヒストグラム（cell 23 後半）。

markov_input TSVのinterval列から、平均・中央値の縦線付きヒストグラムを描く。
スタイルはノートブック版（seaborn whitegrid、Times New Roman、bins=20）を踏襲。

使用例:
    python scripts/plot_inspection_interval.py \
        --input data/processed/markov_input_20251207_200558/markov_input_with_supply.txt \
        --output-stem figures/inspection_interval
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42


def plot_interval_histogram(intervals: pd.Series, output_stem: Path, bins: int = 20) -> list[Path]:
    """点検間隔ヒストグラムを描き、SVG/PDF/PNGで保存する。"""
    try:
        import seaborn as sns

        sns.set_theme(
            style="whitegrid",
            rc={
                "font.family": "serif",
                "font.serif": ["Times New Roman"],
                "axes.facecolor": "white",
            },
        )
        use_seaborn = True
    except ImportError:
        plt.rcParams["font.family"] = "serif"
        use_seaborn = False

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    if use_seaborn:
        import seaborn as sns

        sns.histplot(
            intervals, bins=bins, ax=ax, color="#4C72B0", alpha=0.8,
            edgecolor="#303030", linewidth=1.0, stat="count", element="bars", fill=True,
        )
    else:
        ax.hist(intervals, bins=bins, color="#4C72B0", alpha=0.8,
                edgecolor="#303030", linewidth=1.0)

    mean_val = float(intervals.mean())
    median_val = float(intervals.median())
    ax.axvline(mean_val, color="#FF7F0E", linestyle="--", linewidth=1.6,
               label=f"Mean = {mean_val:.2f}")
    ax.axvline(median_val, color="#2CA02C", linestyle="-.", linewidth=1.6,
               label=f"Median = {median_val:.2f}")
    ax.set_xlabel("Interval (year)")
    ax.set_ylabel("Frequency")
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.grid(axis="y", color="white", linewidth=1, alpha=1.0)
    ax.set_facecolor("#f5f5f5")
    ax.tick_params(axis="x", which="minor", bottom=False)
    ax.tick_params(axis="y", which="minor", left=False)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(frameon=True, framealpha=0.95, edgecolor="#808080", loc="upper right")
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
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/markov_input_20251207_200558/markov_input_with_supply.txt"),
    )
    parser.add_argument("--output-stem", type=Path, default=Path("figures/inspection_interval"),
                        help="出力ファイル名（拡張子なし。png/svg/pdfを生成）")
    parser.add_argument("--bins", type=int, default=20)
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep="\t", encoding="utf-8-sig")
    intervals = pd.to_numeric(df["interval"], errors="coerce").dropna()
    print(f"入力: {args.input}（{len(intervals):,} 件）")
    print(f"mean={intervals.mean():.4f}, median={intervals.median():.1f}, "
          f"min={intervals.min()}, max={intervals.max()}")
    for path in plot_interval_histogram(intervals, args.output_stem, bins=args.bins):
        print(f"保存: {path}")


if __name__ == "__main__":
    main()
