"""JAAM和文・2段組用の図10種類（図7は2枚）と表データを一括生成する。

Usage: python JAAM/make_jaam_figures.py
Outputs: JAAM/figures/*.png, *.pdf, *.svg and optimization_table.csv
図の幅は本文1段の7.6 cmで作る。Wordには幅7.6 cmで配置すること。
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Patch
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
sys.path.insert(0, str(ROOT / "src"))

from bundling_analysis.expected_contracts import (
    DEFAULT_TRANSITION_MATRIX, repair_probability_from_transition_matrix,
)

WIDTH = 7.6 / 2.54
L_COLORS = {1: "#6b7280", 3: "#4c6fb1", 5: "#238b8e", 7: "#cc6c3b", 10: "#7a4e9e"}
M_COLORS = {1: "#6b7280", 2: "#4c6fb1", 3: "#238b8e", 4: "#cc6c3b", 5: "#7a4e9e", 6: "#b0435b"}
MAP_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c"]
GRAY = "#6b7280"
PALETTE = ["#3668a0", "#c96c37", "#288a87", "#7755a1", "#b14b65", "#6e8529"]
MUNICIPALITIES = ["白石市", "大河原町", "蔵王町", "村田町", "川崎町", "七ヶ宿町"]


def setup() -> None:
    candidates = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic",
                  "Noto Sans CJK JP", "IPAexGothic"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    family = next((f for f in candidates if f in available), None)
    if not family:
        raise RuntimeError("日本語フォントが見つかりません。CJKフォントを導入してください。")
    plt.rcParams.update({
        "font.family": family, "font.size": 7.5, "axes.labelsize": 7.5,
        "xtick.labelsize": 7.0, "ytick.labelsize": 7.0,
        "legend.fontsize": 6.5, "axes.unicode_minus": False,
        # WordのSVG取込で日本語フォントの置換・改行が起きないよう、
        # SVG内の文字は輪郭に変換する。PNG/PDFも同じサイズで出力する。
        "pdf.fonttype": 42, "svg.fonttype": "path",
    })
    OUT.mkdir(exist_ok=True)
    print(f"日本語フォント: {family}")


def canvas(height: float = 2.2):
    fig, ax = plt.subplots(figsize=(WIDTH, height))
    return fig, ax


def save(fig, name: str) -> None:
    fig.tight_layout(pad=0.35)
    if name == "expected_contracts_by_bundle_limit":
        # 回転した数式の縦軸名はtight_layoutだけでは幅を確保できない。
        fig.subplots_adjust(left=0.27)
    for ext, kw in (("png", {"dpi": 400}), ("pdf", {}), ("svg", {})):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, **kw)
        if ext == "svg":
            # Matplotlibのpath属性の改行末尾に残る空白を取り除く。
            svg = path.read_text(encoding="utf-8")
            path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n",
                            encoding="utf-8")
    plt.close(fig)
    print(name)


def boundary_polygons():
    geo = json.loads((ROOT / "data/processed/target_municipalities_boundary.geojson").read_text())
    bounds = [float("inf"), float("inf"), -float("inf"), -float("inf")]
    rings = []
    for feature in geo["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            ring = np.asarray(polygon[0])
            rings.append(ring)
            bounds = [min(bounds[0], ring[:, 0].min()), min(bounds[1], ring[:, 1].min()),
                      max(bounds[2], ring[:, 0].max()), max(bounds[3], ring[:, 1].max())]
    return rings, bounds


def draw_boundaries(ax, *, fill=True):
    rings, bounds = boundary_polygons()
    for ring in rings:
        ax.fill(ring[:, 0], ring[:, 1], facecolor="#f6f6f3" if fill else "none",
                edgecolor="#666", linewidth=0.6, zorder=2 if not fill else 1)
    return bounds


def study_area(bridges: pd.DataFrame) -> None:
    fig, ax = canvas(3.0)
    ax.grid(False)
    minx, miny, maxx, maxy = draw_boundaries(ax)
    for i, muni in enumerate(MUNICIPALITIES):
        sub = bridges[bridges["管理者"] == muni]
        ax.scatter(sub["経度"], sub["緯度"], s=8, color=PALETTE[i],
                   edgecolors="white", linewidths=0.15, label=f"{muni} {len(sub)}橋", zorder=3)
    ax.set_xlim(minx - 0.02, maxx + 0.02)
    ax.set_ylim(miny - 0.02, maxy + 0.02)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2,
              frameon=False, markerscale=1.5, columnspacing=0.6,
              handletextpad=0.35, borderaxespad=0)
    save(fig, "study_area")


def inspection() -> None:
    path = ROOT / "data/processed/markov_input_20251207_200558/markov_input_with_supply_collapse.txt"
    intervals = pd.to_numeric(pd.read_csv(path, sep="\t")["interval"], errors="coerce").dropna()
    fig, ax = canvas(2.05)
    ax.hist(intervals, bins=20, color="#4c6fb1", edgecolor="white", linewidth=0.6)
    ax.axvline(float(intervals.mean()), color="#cc6c3b", linewidth=1.4,
               linestyle="--", label=f"平均 = {intervals.mean():.2f}年")
    ax.axvline(float(intervals.median()), color="#238b8e", linewidth=1.4,
               linestyle="-.", label=f"中央値 = {intervals.median():.2f}年")
    ax.set(xlabel="点検間隔（年）", ylabel="遷移件数", xlim=(0, 31))
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#d1d5db", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right", fontsize=6.5)
    save(fig, "inspection_interval")


def scaling(scaling_data: pd.DataFrame) -> None:
    d = scaling_data
    n = d["N"]
    fig, ax = canvas(2.55)
    ax.plot(n, d["probability_two_or_more_demands"], color="#4c6fb1", linewidth=2)
    ax.axvline(322, color=GRAY, linestyle=(0, (5, 3)), linewidth=1.2)
    for count in [50, 100, 200, 322]:
        value = float(d.loc[d.N == count, "probability_two_or_more_demands"].iloc[0])
        ax.plot(count, value, "o", color="#1f2937", markersize=4.5)
        offset = (6, -12 if count == 322 else 6)
        ax.annotate(f"N={count}: {value:.3f}", (count, value), xytext=offset,
                    textcoords="offset points", fontsize=6.5, color="#1f2937")
    ax.set(xlabel="管理エリア内の橋梁数 N（橋）", ylabel=r"複数補修需要の発生確率 $\Pr(X\geq 2)$",
           xlim=(0, 1000), ylim=(0, 1.02))
    ax.grid(color="#d1d5db", linewidth=0.7)
    save(fig, "expected_contracts_scaling_analysis_a")

    fig, ax = canvas(2.65)
    for lim in [3, 5, 7, 10]:
        color = L_COLORS[lim]
        ax.plot(n, d[f"reduction_rate_L{lim}"], color=color,
                linewidth=2, label=f"L={lim}")
        ax.axhline(1 - 1 / lim, color=color, linestyle=(0, (1.5, 1.5)), linewidth=1.2)
    ax.axvline(322, color=GRAY, linestyle=(0, (5, 3)), linewidth=1.2)
    value = float(d.loc[d.N == 322, "reduction_rate_L5"].iloc[0])
    ax.plot(322, value, "o", color="#1f2937", markersize=5)
    ax.annotate(f"N=322, L=5: {value:.3f}", (322, value), xytext=(8, -20),
                textcoords="offset points", fontsize=6.5)
    ax.plot([], [], color=GRAY, linestyle=(0, (1.5, 1.5)), linewidth=1.2,
            label="1−1/L（理論上限）")
    ax.set(xlabel="管理エリア内の橋梁数 N（橋）", ylabel="期待契約件数の低減率 ρ",
           xlim=(0, 1000), ylim=(0, 1.02))
    ax.grid(color="#d1d5db", linewidth=0.7)
    ax.legend(frameon=False, loc="lower right", fontsize=6.5, labelspacing=0.3)
    save(fig, "expected_contracts_scaling_analysis_b")

    fig, ax = canvas(2.25)
    for level in [0.50, 0.75, 0.80, 0.90, 0.95]:
        ax.axhline(level, color="#d1d5db", linewidth=0.8)
        ax.annotate(f"{level:.0%}", (1000, level), xytext=(-2, 3),
                    textcoords="offset points", ha="right", fontsize=6.5, color=GRAY)
    for lim in [3, 5, 7, 10]:
        ax.plot(n, d[f"saturation_rate_L{lim}"], color=L_COLORS[lim],
                linewidth=2, label=f"L={lim}")
    ax.axvline(322, color=GRAY, linestyle=(0, (5, 3)), linewidth=1.2)
    value = float(d.loc[d.N == 322, "saturation_rate_L5"].iloc[0])
    ax.plot(322, value, "o", color="#1f2937", markersize=5)
    ax.annotate(f"N=322, L=5: {value:.1%}", (322, value), xytext=(8, -18),
                textcoords="offset points", fontsize=6.5)
    ax.set(xlabel="管理エリア内の橋梁数 N（橋）", ylabel="理論上限への到達率 η",
           xlim=(0, 1000), ylim=(0, 1.02))
    ax.grid(axis="x", color="#d1d5db", linewidth=0.7)
    ax.legend(frameon=False, loc="lower right", ncol=2, fontsize=6.5)
    save(fig, "expected_contracts_saturation")

    fig, ax = canvas(2.25)
    q = float(d["repair_probability_q"].iloc[0])
    ax.plot(n, n * q, color=L_COLORS[1], linestyle="-", linewidth=1.6, label="L=1")
    for lim, style in [(3, "--"), (5, "-"), (7, "-."), (10, ":")]:
        ax.plot(n, d[f"expected_contracts_L{lim}"], color=L_COLORS[lim],
                linestyle=style, linewidth=1.6, label=f"L={lim}")
    ax.set(xlabel="管理エリア内の橋梁数 N（橋）", ylabel="f(N,L)（件／年）",
           xlim=(0, 342), ylim=(0, 4.2))
    ax.legend(frameon=False, loc="upper left", fontsize=6.5)
    save(fig, "expected_contracts_by_bundle_limit")


def sensitivity(results: pd.DataFrame, baseline: float) -> None:
    fig, ax = canvas(2.4)
    markers = {1: "o", 2: "s", 3: "^", 4: "D", 5: "v", 6: "P"}
    for m in sorted(results["M"].unique()):
        sub = results[results["M"] == m].sort_values("MaxDistance")
        ax.plot(sub["MaxDistance"], sub["ObjectiveValue_Exact"],
                color=M_COLORS[int(m)], marker=markers[int(m)], markersize=3.5,
                linewidth=1.25, label=f"{int(m)}エリア")
    ax.axhline(baseline, color=GRAY, linestyle="--", linewidth=1,
               label="現行6市町")
    ax.set(xlabel="エリア内の距離上限 D（km）", ylabel="年間期待契約件数（件）",
           xlim=(13, 52), ylim=(1.1, 2.75))
    ax.set_xticks([15, 25, 35, 45])
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.0),
              columnspacing=0.7, handlelength=1.5, borderpad=0.1)
    save(fig, "dm_sensitivity")

    zoom = results[results.MaxDistance >= 40]
    fig, ax = canvas(2.55)
    for m in sorted(zoom.M.unique()):
        sub = zoom[zoom.M == m].sort_values("MaxDistance")
        ax.plot(sub.MaxDistance, sub.ObjectiveValue_Exact,
                color=M_COLORS[int(m)], marker=markers[int(m)], markersize=5,
                markeredgecolor="white", markeredgewidth=0.35,
                linewidth=1.4, label=f"M={int(m)}")
    ax.set(xlabel="距離上限 D（km）", ylabel="年間期待契約件数 Z（件）",
           xlim=(38.5, 51.5), ylim=(1.185, 1.255))
    ax.set_xticks([40, 45, 50])
    ax.grid(color="#d1d5db", linewidth=0.7)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18),
              columnspacing=0.7, handlelength=1.5, fontsize=6.5)
    save(fig, "dm_sensitivity_b")


def breakdown() -> None:
    d = pd.read_csv(ROOT / "outputs/region_breakdown.csv")
    cases = [(25, 3, "D=25 km\nM=3"), (30, 2, "D=30 km\nM=2"), (40, 1, "D=40 km\nM=1")]
    fig, ax = canvas(2.25)
    totals = []
    for j, (dist, m, label) in enumerate(cases):
        rows = d[(d.D == dist) & (d.M == m)].sort_values("region_rank")
        bottom = 0
        for i, r in enumerate(rows.itertuples(index=False)):
            ax.bar(j, r.f_Nm, bottom=bottom, width=0.6, color=M_COLORS[i + 1],
                   edgecolor="white", linewidth=0.6, zorder=2)
            if r.f_Nm > 0.04:
                ax.text(j, bottom + r.f_Nm / 2, rf"$N_{{{i+1}}}={r.N_m}$", ha="center",
                        va="center", fontsize=6.5, color="white")
            bottom += r.f_Nm
        totals.append(bottom)
        ax.text(j, bottom + 0.02, f"{bottom:.3f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(3), [x[2] for x in cases])
    ax.set(ylabel="年間期待契約件数（件）", ylim=(0, max(totals) * 1.13))
    ax.grid(axis="y", color="#d1d5db", linewidth=0.7)
    ax.set_axisbelow(True)
    save(fig, "region_breakdown")


def voronoi_image(coords: np.ndarray, clusters: np.ndarray, bounds, rings):
    """元図と同じ最近接橋梁によるVoronoi面を格子上で描く。"""
    minx, miny, maxx, maxy = bounds
    nx = 420
    ny = int(nx * (maxy - miny) / (maxx - minx))
    xs = np.linspace(minx, maxx, nx)
    ys = np.linspace(miny, maxy, ny)
    xx, yy = np.meshgrid(xs, ys)
    points = np.column_stack([xx.ravel(), yy.ravel()])
    inside = np.zeros(len(points), dtype=bool)
    for ring in rings:
        inside |= MplPath(ring).contains_points(points)
    # 経度と緯度を概ね同じ距離尺度へ変換する。
    scale_x = np.cos(np.deg2rad(np.mean(coords[:, 1])))
    nearest = np.empty(len(points), dtype=np.int16)
    for start in range(0, len(points), 2000):
        p = points[start:start + 2000]
        distance2 = ((p[:, None, 0] - coords[None, :, 0]) * scale_x) ** 2 + \
                    (p[:, None, 1] - coords[None, :, 1]) ** 2
        nearest[start:start + 2000] = np.argmin(distance2, axis=1)
    rgba = np.zeros((ny * nx, 4), dtype=float)
    from matplotlib.colors import to_rgb
    for cluster in range(int(clusters.max()) + 1):
        mask = inside & (clusters[nearest] == cluster)
        rgba[mask, :3] = to_rgb(MAP_COLORS[cluster])
        rgba[mask, 3] = 0.34
    return rgba.reshape(ny, nx, 4)


def districting(d: int, m: int) -> None:
    with (ROOT / "data/processed/districting_solutions_all36.pkl").open("rb") as f:
        solutions = pickle.load(f)
    assignment = solutions[(float(d), m)]["assignment"]
    with (ROOT / "data/processed/distance_matrix_322_20251208.pkl").open("rb") as f:
        order = pickle.load(f)["order"]
    bridges = pd.read_csv(ROOT / "data/processed/target_rc_bridges_322.csv")
    aligned = bridges.assign(_sid=bridges["shisetsu_id"].astype(str)).set_index("_sid").loc[order]
    coords = aligned[["経度", "緯度"]].to_numpy()
    clusters = np.argmax(assignment, axis=1)
    ranks = sorted(range(m), key=lambda c: -int((clusters == c).sum()))
    fig, ax = canvas(2.8)
    rings, bounds = boundary_polygons()
    minx, miny, maxx, maxy = bounds
    image = voronoi_image(coords, clusters, bounds, rings)
    ax.imshow(image, origin="lower", extent=(minx, maxx, miny, maxy),
              interpolation="nearest", zorder=1)
    draw_boundaries(ax, fill=False)
    for cluster in range(m):
        pts = coords[clusters == cluster]
        ax.scatter(pts[:, 0], pts[:, 1], s=9, color=MAP_COLORS[cluster],
                   edgecolor="white", linewidth=0.15, zorder=3)
    ax.set_xlim(minx - 0.02, maxx + 0.02); ax.set_ylim(miny - 0.02, maxy + 0.02)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.spines[:].set_visible(False)
    handles = [Patch(facecolor=MAP_COLORS[c], alpha=0.55,
                     label=f"エリア{i+1}：{int((clusters == c).sum())}橋")
               for i, c in enumerate(ranks)]
    ax.legend(handles=handles, frameon=False, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.01), columnspacing=0.7,
              handlelength=1.2, borderaxespad=0)
    save(fig, f"districting_map_D{d}_M{m}")


def main() -> None:
    setup()
    bridges = pd.read_csv(ROOT / "data/processed/target_rc_bridges_322.csv")
    if len(bridges) != 322:
        raise ValueError("対象橋梁数が322ではありません")
    study_area(bridges)
    inspection()
    scaling(pd.read_csv(ROOT / "outputs/expected_contracts_scaling_analysis.csv"))
    results = pd.read_csv(ROOT / "data/processed/optimization_results_exact_objective.csv")
    results = results[results.Status == 2]
    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    if not 0.0122 < q < 0.0125:
        raise ValueError("補修需要確率が論文の条件と異なります")
    baseline = float(pd.read_csv(ROOT / "outputs/optimization_results_table.csv").iloc[0]["ObjectiveValue_Exact"])
    sensitivity(results, baseline)
    breakdown()
    districting(25, 3)
    districting(30, 2)
    table = pd.read_csv(ROOT / "outputs/optimization_results_table.csv")
    table.to_csv(OUT / "optimization_table.csv", index=False)


if __name__ == "__main__":
    main()
