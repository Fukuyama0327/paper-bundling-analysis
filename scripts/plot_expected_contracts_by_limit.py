"""Plot the closed-form expected contract count for several bundle limits.

The figure is a numerical illustration of the analytical function f(N, L)
used in the optimization; it does not use simulation results.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.plotting_utils import figure_size, setup_figure_defaults  # noqa: E402

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
# 多くの学術誌がType 3を受け付けないため、保存前に必ず適用する。
setup_figure_defaults()

from bundling_analysis.expected_contracts import (  # noqa: E402
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-n", type=int, default=322)
    parser.add_argument("--bundle-limits", type=int, nargs="+", default=[1, 3, 5, 7, 10])
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=Path("figures/expected_contracts_by_bundle_limit"),
    )
    args = parser.parse_args()

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    n_values = list(range(1, args.max_n + 1))

    fig, ax = plt.subplots(figsize=figure_size(0.78, aspect=0.64))
    # L が大きいほど曲線が重なる（L=7 と L=10 はほぼ一致する）ので、色だけでなく
    # 線種も変えて区別する。査読で「色分けが見づらい」と指摘された（2026-09-25）。
    colors = ["#6b7280", "#4c6fb1", "#238b8e", "#cc6c3b", "#7a4e9e"]
    styles = ["-", "--", "-", "-.", ":"]
    for limit, color, style in zip(args.bundle_limits, colors, styles):
        y_values = [expected_contracts(n, limit, q) for n in n_values]
        ax.plot(n_values, y_values, linewidth=1.6, color=color, linestyle=style,
                label=rf"$L={limit}$")

    ax.set_xlabel("Number of bridges in a management area, $N$")
    ax.set_ylabel("Expected annual number of contracts, $f(N,L)$")
    ax.set_xlim(0, args.max_n + 20)
    ax.set_ylim(bottom=0)
    # グリッド線は引かない。枠なし凡例の文字を横切って読みにくくなるため
    # （査読コメント「グリッド線は不要かも、最低限、凡例と被らないように」）。
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
