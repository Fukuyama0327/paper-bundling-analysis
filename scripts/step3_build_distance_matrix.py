# -*- coding: utf-8 -*-
"""STEP3-4: 対象橋梁の距離行列を構築する。

`20251206.ipynb` cell 30 の再実装。SQLiteキャッシュ（distance_cache.py）に
一本化し、ノートブック独自の `cache/dist_matrices/*.pkl` キャッシュ層は廃止
（notes/pre_git_migration_inventory.md 7-2章-5）。出力pklは明示的な成果物
（`run_gurobi_districting.py` の入力）であり、暗黙キャッシュではない。

なお、既存の `data/processed/distance_matrix_322_20251208.pkl` はそのまま
使い回す方針（共有キャッシュ dist_cache.sqlite 6.6GBへの依存があるため。
2-2章）。本スクリプトは頭から再構築が必要になった場合の再現手順を残すもの。

使用例:
    python scripts/step3_build_distance_matrix.py \
        --input data/processed/target_rc_bridges_322.csv \
        --output data/processed/distance_matrix_322.pkl \
        [--db-path /path/to/dist_cache.sqlite]
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.distance_cache import ensure_db, get_distance_matrix, upsert_nodes


def build_distance_matrix(
    df: pd.DataFrame, db_path: str | None = None
) -> tuple[list[str], np.ndarray]:
    """橋梁DataFrameから代表ノードの距離行列を構築する。

    Returns
    -------
    (order, d_core):
        order は代表bridge_id（shisetsu_id文字列）のリスト、
        d_core は同順の距離行列（km）。
    """
    df = df.dropna(subset=["緯度", "経度"]).reset_index(drop=True)
    df = df.copy()
    df["bridge_id"] = df["shisetsu_id"].astype(str)
    unique_bridge_ids = list(dict.fromkeys(df["bridge_id"]))
    print(f"[dist] 代表ノード数: {len(unique_bridge_ids)} / 全体 {len(df)}橋")

    conn = ensure_db(db_path) if db_path else ensure_db()
    try:
        nodes = []
        pref_col = "syogen.gyousei_kuiki.todoufuken_mei"
        for rec in df.drop_duplicates("bridge_id").to_dict("records"):
            try:
                lat, lon = float(rec["緯度"]), float(rec["経度"])
            except (TypeError, ValueError):
                continue
            if np.isnan(lat) or np.isnan(lon):
                continue
            node = {"bridge_id": rec["bridge_id"], "lat": lat, "lon": lon}
            for src, dst in [("橋名", "name"), ("管理者", "admin"), (pref_col, "prefecture")]:
                value = rec.get(src)
                if pd.notna(value):
                    node[dst] = value
            nodes.append(node)
        if nodes:
            inserted = upsert_nodes(conn, nodes)
            print(f"[dist] upsert_nodes 完了: {inserted}行処理")

        t0 = time.perf_counter()
        d_core, order = get_distance_matrix(conn, unique_bridge_ids)
        if order != unique_bridge_ids:
            index = {bid: i for i, bid in enumerate(order)}
            reorder = [index[bid] for bid in unique_bridge_ids]
            d_core = d_core[np.ix_(reorder, reorder)]
            order = unique_bridge_ids
        print(f"[dist] 距離行列取得完了: {time.perf_counter() - t0:.2f}s")
    finally:
        conn.close()

    n_zero = int(((d_core <= 0) & ~np.eye(len(order), dtype=bool)).sum()) // 2
    if n_zero:
        print(f"[warn] 距離が未計算または0の非対角ペアが {n_zero} 件あります（同一座標の可能性）")
    return order, d_core


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="対象橋梁CSV（shisetsu_id・緯度・経度列必須）")
    parser.add_argument("--output", required=True, help="出力pklパス（{'order', 'd_core'} 形式）")
    parser.add_argument("--db-path", default=None, help="dist_cache.sqlite のパス（省略時はデフォルト）")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    order, d_core = build_distance_matrix(df, db_path=args.db_path)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        pickle.dump({"order": order, "d_core": d_core}, f)
    print(f"保存: {out}（{len(order)}×{len(order)}）")


if __name__ == "__main__":
    main()
