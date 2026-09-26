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

#: 他の図の配色（plotting_utils の M_COLORS）と同系統に揃える。
HIST_COLOR = "#4c6fb1"
MEAN_COLOR = "#cc6c3b"
MEDIAN_COLOR = "#238b8e"


def plot_interval_histogram(intervals: pd.Series, output_stem: Path, bins: int = 20) -> list[Path]:
    """点検間隔ヒストグラムを描き、SVG/PDF/PNGで保存する。

    以前は seaborn の ``whitegrid`` テーマを当て、さらに軸の背景を ``#f5f5f5`` で
    塗っていた。そのためこの図だけ灰色地・白いグリッド線・枠付き凡例という
    別系統の見た目になり、査読で「灰色背景を白色に、全てのグラフでデザインが
    大きく異ならないように」と指摘された（2026-09-25）。seaborn は書体設定まで
    上書きするので、依存ごと外して他の図と同じ素の matplotlib に揃えてある。
    """
    fig, ax = plt.subplots(figsize=figure_size(0.75, aspect=0.60))
    ax.hist(intervals, bins=bins, color=HIST_COLOR, edgecolor="white", linewidth=0.6)

    mean_val = float(intervals.mean())
    median_val = float(intervals.median())
    ax.axvline(mean_val, color=MEAN_COLOR, linestyle="--", linewidth=1.4,
               label=f"Mean = {mean_val:.2f}")
    ax.axvline(median_val, color=MEDIAN_COLOR, linestyle="-.", linewidth=1.4,
               label=f"Median = {median_val:.2f}")
    ax.set_xlabel("Inspection interval (years)")
    ax.set_ylabel("Number of transitions")
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    # 他の図と同じ薄いグリッド・枠なし凡例にする。
    ax.grid(axis="y", color="#d1d5db", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", which="minor", bottom=False)
    ax.tick_params(axis="y", which="minor", left=False)
    ax.legend(frameon=False, loc="upper right")
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
        default=Path("data/processed/markov_input_20251207_200558/markov_input_with_supply_collapse.txt"),
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
