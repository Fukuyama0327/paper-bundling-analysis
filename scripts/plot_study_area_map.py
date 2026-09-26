"""Study-area map: the six target municipalities and their 322 RC bridges.

Draws the municipal boundaries of the six target municipalities (background) and
the 322 target bridges coloured by managing municipality. Intended as the opening
"study area" figure of the numerical section. Municipality names are romanised so
the figure needs no Japanese font. This absorbs the role of the prefecture-wide
manager bar chart (source notebook cell 10), which is out of scope here.
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

from bundling_analysis.admin_boundary import load_admin_boundaries_gdf  # noqa: E402

#: Target municipalities and their romanised names (kanji -> Latin) + fixed colour.
MUNICIPALITIES = ["白石市", "大河原町", "蔵王町", "村田町", "川崎町", "七ヶ宿町"]
ROMAJI = {
    "白石市": "Shiroishi",
    "大河原町": "Ogawara",
    "蔵王町": "Zao",
    "村田町": "Murata",
    "川崎町": "Kawasaki",
    "七ヶ宿町": "Shichikashuku",
}
COLORS = {
    "白石市": "#4c6fb1",
    "大河原町": "#cc6c3b",
    "蔵王町": "#238b8e",
    "村田町": "#7a4e9e",
    "川崎町": "#b0435b",
    "七ヶ宿町": "#6b8e23",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bridges", type=Path,
                        default=Path("data/processed/target_rc_bridges_322.csv"))
    parser.add_argument(
        "--boundary",
        type=Path,
        default=Path("data/processed/target_municipalities_boundary.geojson"),
        help="6市町の行政界（既定は同梱の派生geojson。config.SHAPEFILE_PATHの全国shpでも可）。",
    )
    parser.add_argument("--output-stem", type=Path, default=Path("figures/study_area"))
    args = parser.parse_args()

    gdf, union = load_admin_boundaries_gdf(args.boundary, municipalities=MUNICIPALITIES)
    if gdf is None:
        raise SystemExit(f"行政界が読み込めません: {args.boundary}")

    df = pd.read_csv(args.bridges)
    counts = df["管理者"].value_counts()
    print(f"bridges plotted = {len(df)} (sum of municipality counts = {int(counts.sum())})")

    fig, ax = plt.subplots(figsize=figure_size(0.82, aspect=0.95))
    gdf.plot(ax=ax, facecolor="#f4f4f2", edgecolor="#555555", linewidth=1.0, zorder=1)

    # 凡例の記号を本文の記法に合わせる。現行の行政区割りは6市町＝6つの管理エリアなので、
    # 各市町の橋梁数は N_k で表せる。索引は本文の N_1 >= N_2 >= ... という規約に従い、
    # 橋梁数の降順で振る（査読コメント 2026-09-25）。
    ordered = sorted(MUNICIPALITIES, key=lambda m: -(df["管理者"] == m).sum())
    for index, muni in enumerate(ordered, start=1):
        sub = df[df["管理者"] == muni]
        # マーカーは少し大きく（同コメント）。
        ax.scatter(sub["経度"], sub["緯度"], s=22, color=COLORS[muni], edgecolor="white",
                   linewidth=0.35, zorder=3,
                   label=rf"{ROMAJI[muni]} ($N_{{{index}}}={len(sub)}$)")

    minx, miny, maxx, maxy = union.bounds
    mx, my = (maxx - minx) * 0.03, (maxy - miny) * 0.03
    ax.set_xlim(minx - mx, maxx + mx)
    ax.set_ylim(miny - my, maxy + my)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    # 凡例は地図の外（下）へ出す。枠内に置くと橋梁プロットに重なる（同コメント）。
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3,
              handletextpad=0.4, columnspacing=1.6,
              title=rf"Managing municipality ($|\mathcal{{I}}|={len(df)}$)")
    fig.tight_layout()

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = args.output_stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)

    if int(counts.sum()) != len(df) or len(df) != 322:
        raise SystemExit("検証失敗: 橋梁数が322/市町別合計と一致しません。")


if __name__ == "__main__":
    main()
