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

from bundling_analysis.plotting_utils import (  # noqa: E402
    M_COLORS,
    M_MARKER_SIZE_SCALE,
    M_MARKERS,
    figure_size,
    setup_figure_defaults,
)

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
# 多くの学術誌がType 3を受け付けないため、保存前に必ず適用する。
setup_figure_defaults()

#: 右パネルで拡大する距離上限の下限。この値以上では距離制約が対象322橋の
#: 直径に達して効かなくなり、目的関数値は M だけで決まる。
ZOOM_FROM = 40.0

from bundling_analysis.expected_contracts import (  # noqa: E402
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)


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

    # (a) 全体、(b) 距離制約が効かなくなる D>=40 の拡大の2枚組にする。
    # 1枚に収めると、M 違いの差（D を固定すると 0.001〜0.01 程度）が潰れて
    # 1本の線に見える。拡大を別パネルに出せば M の順序が読める
    # （査読コメント「線が重複して見づらい」2026-09-25 への対応）。
    fig, (ax_all, ax_zoom) = plt.subplots(1, 2, figsize=figure_size(1.0, aspect=0.44))

    def draw(ax, data, *, with_baseline: bool) -> None:
        if with_baseline:
            ax.axhline(baseline, color="#333333", linestyle=(0, (5, 3)), linewidth=1.2,
                       label=f"Current districting ({baseline:.4f})")
        for m in sorted(data["M"].unique()):
            sub = data[data["M"] == m].sort_values("MaxDistance")
            # 色だけでは読み取れないのでマーカーの形も変える。形と色の対応は
            # pareto_radius など他の図と共通。
            ax.plot(sub["MaxDistance"], sub["ObjectiveValue_Exact"],
                    marker=M_MARKERS.get(int(m), "o"),
                    markersize=4.5 * M_MARKER_SIZE_SCALE.get(int(m), 1.0),
                    markeredgecolor="white", markeredgewidth=0.5,
                    linewidth=1.3, color=M_COLORS.get(int(m), None),
                    label=f"$M = {int(m)}$" if with_baseline else None)
        ax.set_xlabel("Distance limit, $D$ (km)")
        ax.grid(color="#d1d5db", linewidth=0.7)

    # --- (a) 全ケース ---------------------------------------------------------
    draw(ax_all, df, with_baseline=True)
    # 縦軸は各ケースの目的関数値、すなわち総和 Z = sum_k f(N_k, L)。
    # 2枚組ではパネルが狭く、1行だと枠からはみ出すので折り返す。
    ax_all.set_ylabel("Expected annual number\nof contracts, $Z$")
    ax_all.set_xlim(min(df["MaxDistance"]) - 2, max(df["MaxDistance"]) + 2)
    # 0 から描くと M 違いの差が潰れる。基準線から最小値までを使い切る。
    low = float(df["ObjectiveValue_Exact"].min())
    ax_all.set_ylim(low - 0.06, baseline + 0.08)

    # --- (b) D>=40 の拡大 -----------------------------------------------------
    zoom = df[df["MaxDistance"] >= ZOOM_FROM]
    draw(ax_zoom, zoom, with_baseline=False)
    ax_zoom.set_ylabel("Expected annual number\nof contracts, $Z$")
    ax_zoom.set_xlim(ZOOM_FROM - 1.5, float(zoom["MaxDistance"].max()) + 1.5)
    ax_zoom.set_xticks(sorted(zoom["MaxDistance"].unique()))
    zoom_low = float(zoom["ObjectiveValue_Exact"].min())
    zoom_high = float(zoom["ObjectiveValue_Exact"].max())
    pad = (zoom_high - zoom_low) * 0.22
    ax_zoom.set_ylim(zoom_low - pad, zoom_high + pad)

    print("\nPlotted points (D, M, ObjectiveValue_Exact):")
    for m in sorted(df["M"].unique()):
        for _, row in df[df["M"] == m].sort_values("MaxDistance").iterrows():
            print(f"  D={row['MaxDistance']:>4}, M={int(m)}: {row['ObjectiveValue_Exact']:.6f}")

    # 凡例は2枚に共通なので、図全体の下へ1つだけ置く。
    handles, labels = ax_all.get_legend_handles_labels()
    fig.tight_layout()
    fig.legend(handles, labels, frameon=False, ncol=4, loc="upper center",
               bbox_to_anchor=(0.5, 0.07), columnspacing=1.6, handlelength=2.0)

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
