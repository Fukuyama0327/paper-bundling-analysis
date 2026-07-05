# -*- coding: utf-8 -*-
"""宮城県行政界データの統一ローダ。

`20251206.ipynb` では行政界の読み込みが cell 9（旧2018年版shp）、
cell 11（他プロジェクトへの相対パスgeojson）、cell 35・37（2023年版全国shp）の
4箇所・3系統で重複実装されていた（`notes/pre_git_migration_inventory.md`
7-2章-1）。ここに一本化する。

正本は2023年版全国シェープファイル（``N03-23_230101.shp``、
``config.SHAPEFILE_PATH`` が指すもの）とし、旧2018年版は
``load_admin_boundary(path, prefecture=...)`` に旧ファイルのパスを渡せば
同じ関数で読める。
"""

from __future__ import annotations

from pathlib import Path


def load_admin_boundary(
    shapefile_path: str | Path,
    prefecture: str = "宮城県",
    municipalities: list[str] | None = None,
    encoding: str = "shift_jis",
):
    """行政界を読み込み、単一ポリゴン（shapely geometry）を返す。

    Parameters
    ----------
    shapefile_path:
        国土数値情報 N03 のシェープファイル（またはgeojson）パス。
    prefecture:
        都道府県名でフィルタ（``N03_001`` 列）。列が無い場合は全体を使う。
    municipalities:
        指定した場合、市区町村名（``N03_004`` 列）でさらに絞り込む。
    encoding:
        シェープファイルのエンコーディング。UnicodeDecodeError 時は
        utf-8 でリトライする。

    Returns
    -------
    shapely geometry（dissolve + unary_union 済み）。該当ポリゴンが
    見つからない場合は ``None``。
    """
    import geopandas as gpd
    from shapely.ops import unary_union

    path = Path(shapefile_path)
    if not path.exists():
        raise FileNotFoundError(f"行政界ファイルが見つかりません: {path}")

    try:
        gdf = gpd.read_file(path, encoding=encoding)
    except UnicodeDecodeError:
        gdf = gpd.read_file(path, encoding="utf-8")

    if gdf.crs is not None and gdf.crs.to_string().upper() not in ("EPSG:4326", "CRS:84", "CRS84"):
        gdf = gdf.to_crs(epsg=4326)

    if "N03_001" in gdf.columns:
        gdf = gdf[gdf["N03_001"] == prefecture]
    if municipalities is not None and "N03_004" in gdf.columns:
        gdf = gdf[gdf["N03_004"].isin(municipalities)]
    if gdf.empty:
        return None

    dissolved = gdf.dissolve()
    return unary_union(dissolved.geometry)


def filter_points_within(df, boundary, lat_col: str = "緯度", lon_col: str = "経度"):
    """境界ポリゴン内の行だけを残した DataFrame と除外件数を返す（cell 9 由来）。"""
    import geopandas as gpd

    points = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs="EPSG:4326"
    )
    inside = points.geometry.within(boundary)
    removed = int((~inside).sum())
    return df[inside.values].reset_index(drop=True).drop(columns="geometry", errors="ignore"), removed
