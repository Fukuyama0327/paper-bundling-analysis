# -*- coding: utf-8 -*-
"""地域分割地図の描画（Voronoi＋橋梁点）。

`20251122_.../図表作成/visualize_voronoi_from_saved_results.py` の中核2関数
（``bridge_based_voronoi_with_clustering`` / ``plot_voronoi_map``）を移植し、
現行データ（solutions pkl の割当行列・`target_rc_bridges_322.csv`・6市町境界）に
接続できるよう純関数化した。旧実装の絶対パス・旧pkl形式・宮城単一ポリゴンといった
I/O依存は取り除き、ロジック（scipy Voronoi→橋梁ポリゴン抽出→クラスタ統合→境界
クリップ→描画）だけを残している。

橋梁座標は (経度, 緯度) = (x, y) の順で渡す。狭い対象領域なので平面近似で扱う。
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Sequence

import numpy as np


def load_solutions(path: str | Path) -> dict[tuple[float, int], np.ndarray]:
    """solutions pkl を {(D, M): assignment} に正規化して読み込む。

    対応形式:
      1. ``run_gurobi_districting.py`` 形式: ``{(D, M): {'assignment': ..., ...}}``
      2. ノートブック形式: ``{'by_distance': {D: {M: z}}, ...}``
    """
    with Path(path).open("rb") as f:
        data = pickle.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"未対応のpkl形式です: {type(data)}")
    if "by_distance" in data:
        return {(float(d), int(m)): np.asarray(z)
                for d, per_m in data["by_distance"].items() for m, z in per_m.items()}
    out: dict[tuple[float, int], np.ndarray] = {}
    for key, value in data.items():
        d, m = key
        assignment = value["assignment"] if isinstance(value, dict) else value
        out[(float(d), int(m))] = np.asarray(assignment)
    return out


def coords_in_assignment_order(bridges, order) -> np.ndarray:
    """距離行列 order（shisetsu_id 順）に合わせて (経度, 緯度) 配列を返す。

    割当行列の行順は距離行列 pkl の ``order`` に対応する。橋梁CSVの行順は
    それと異なりうるため、``shisetsu_id`` で突き合わせて order に並べ替える。
    """
    order = [str(x) for x in order]
    b = bridges.assign(_sid=bridges["shisetsu_id"].astype(str))
    if sorted(b["_sid"]) != sorted(order):
        raise ValueError("橋梁CSVの shisetsu_id と距離行列 order が同じ集合ではありません。")
    b = b.set_index("_sid").loc[order]
    return np.column_stack([b["経度"].to_numpy(float), b["緯度"].to_numpy(float)])


def _dummy_points(coords: np.ndarray, span: float = 10.0) -> np.ndarray:
    """外周セルを閉じるための四隅ダミー点（旧実装と同じ発想）。"""
    center = np.mean(coords, axis=0)
    return np.array([
        center + [span, span],
        center + [span, -span],
        center + [-span, -span],
        center + [-span, span],
    ])


def bridge_based_voronoi(coords, assigned_clusters, boundary_geom=None, min_area: float = 1e-6):
    """橋梁座標ベースの Voronoi を生成し、クラスタIDごとにポリゴン統合＋境界クリップ。

    Returns dict[cluster_id -> {'polygon', 'bridge_count', 'total_area'}]。
    ``visualize_voronoi_from_saved_results.bridge_based_voronoi_with_clustering`` の移植。
    """
    from scipy.spatial import Voronoi
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    coords = np.asarray(coords, dtype=float)
    assigned_clusters = np.asarray(assigned_clusters)
    dummy = _dummy_points(coords)
    all_points = np.vstack([coords, dummy])
    vor = Voronoi(all_points)

    bridge_polygons: dict[int, "Polygon"] = {}
    for bridge_idx in range(len(coords)):
        region_idx = vor.point_region[bridge_idx]
        region = vor.regions[region_idx]
        if not region or -1 in region:
            continue
        try:
            poly = Polygon([vor.vertices[v] for v in region])
            if poly.area >= min_area:
                bridge_polygons[bridge_idx] = poly
        except Exception:
            continue

    cluster_polygons: dict[int, dict] = {}
    for cluster_id in np.unique(assigned_clusters):
        idx = np.where(assigned_clusters == cluster_id)[0]
        polys = [bridge_polygons[i] for i in idx if i in bridge_polygons]
        if not polys:
            continue
        try:
            union = polys[0] if len(polys) == 1 else unary_union(polys).buffer(0)
            if boundary_geom is not None:
                clipped = boundary_geom.intersection(union)
                if clipped.is_empty or clipped.area < min_area:
                    continue
                final = clipped
            else:
                final = union
            cluster_polygons[int(cluster_id)] = {
                "polygon": final,
                "bridge_count": int(len(idx)),
                "total_area": float(final.area),
            }
        except Exception:
            continue
    return cluster_polygons


def region_colors(n_regions: int):
    """地域index→固定色（全図で統一）。最大10地域まで tab10。"""
    import matplotlib.pyplot as plt

    cmap = plt.cm.tab10
    return [cmap(i % 10) for i in range(n_regions)]


def plot_voronoi_map(
    cluster_polygons: dict,
    coords,
    assigned_clusters,
    boundary_gdf=None,
    bounds: Sequence[float] | None = None,
    title: str | None = None,
    ax=None,
    show_legend: bool = True,
    point_size: float = 14.0,
):
    """Voronoi ポリゴン＋橋梁点（ともに地域色）を描く。

    ``visualize_voronoi_from_saved_results.plot_voronoi_map`` の移植＋改修:
    橋梁点を赤単色→地域色に、背景を6市町境界に、色は地域index固定、英語ラベル。
    ``ax`` を渡すと（atlas の小図用に）そこへ描画する。
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    coords = np.asarray(coords, dtype=float)
    assigned_clusters = np.asarray(assigned_clusters)
    n_regions = int(assigned_clusters.max()) + 1
    colors = region_colors(n_regions)

    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(7.6, 7.2))
    else:
        fig = ax.get_figure()

    if boundary_gdf is not None:
        boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="#555555", linewidth=0.9, zorder=1)

    legend_elements = []
    for cluster_id, info in sorted(cluster_polygons.items()):
        color = colors[cluster_id % len(colors)]
        poly = info["polygon"]
        parts = [poly] if poly.geom_type == "Polygon" else list(getattr(poly, "geoms", []))
        for p in parts:
            x, y = p.exterior.xy
            ax.fill(x, y, alpha=0.35, fc=color, ec=color, linewidth=1.2, zorder=2)
        legend_elements.append(
            mpatches.Patch(facecolor=color, edgecolor=color, alpha=0.6,
                           label=f"Region {cluster_id + 1} ({info['bridge_count']})")
        )

    for cid in range(n_regions):
        m = assigned_clusters == cid
        if not m.any():
            continue
        ax.scatter(coords[m, 0], coords[m, 1], s=point_size, color=colors[cid % len(colors)],
                   edgecolor="white", linewidth=0.3, zorder=4)

    if bounds is not None:
        minx, miny, maxx, maxy = bounds
        mx, my = (maxx - minx) * 0.03, (maxy - miny) * 0.03
        ax.set_xlim(minx - mx, maxx + mx)
        ax.set_ylim(miny - my, maxy + my)
    ax.set_aspect("equal", adjustable="box")
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold")
    if show_legend:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend(handles=legend_elements, loc="upper right", fontsize=9, frameon=True)
        ax.grid(color="#e0e0e0", linewidth=0.6)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    return fig, ax
