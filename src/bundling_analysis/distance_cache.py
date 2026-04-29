#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
距離行列キャッシュ モジュール（SQLite + NumPy）

- 依存: 標準ライブラリ + numpy（pandasは任意）
- DB: SQLite（WAL有効化、バッチコミット対応）

機能:
- ensure_db(db_path): DB初期化（スキーマ作成、WAL設定）
- upsert_nodes(df_or_list): ノード（橋梁）情報の一括登録
- get_coords(ids): ノード座標の取得
- get_or_compute_pairs(pairs, metric): ペア距離の取得／未計算分のみ一括計算→保存
- get_distance_matrix(ids, metric): 指定IDの距離行列（未計算分は自動補完）
- get_edges_within(ids, D_km, metric): しきい値内のエッジを返す

距離メトリック:
- haversine_km（地球半径=6371.0088km）

キーポイント:
- ノードキー: bridge_id（例: shisetsu_id）
- 距離キーは (a,b,metric,coords_hash_a,coords_hash_b) を主キー化（a<bに正規化）
- coords_hash は lat/lon を丸めた文字列の SHA1 で生成（座標変更に強い）
"""

from __future__ import annotations

import os
import sqlite3
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Optional, Dict, Any

import numpy as np

def _resolve_default_db_path() -> str:
    """Shared SQLite path used across notebooks.

    Preference order:
    1. Environment variable ``DIST_CACHE_DB_PATH`` (absolute/relative).
    2. ``03_研究テーマ検討/dist_cache/dist_cache.sqlite`` if the structure is detected.
    3. Legacy location ``results/dist_cache.sqlite`` under the current project.
    """

    env_path = os.getenv("DIST_CACHE_DB_PATH")
    if env_path:
        return os.path.abspath(os.path.expanduser(env_path))

    current = Path(__file__).resolve()
    shared_root: Optional[Path] = None
    for parent in current.parents:
        if parent.name == "03_研究テーマ検討":
            shared_root = parent / "dist_cache"
            break

    if shared_root is None:
        # Fallback to previous behaviour inside each project directory.
        legacy_root = current.parent.parent / "results"
        return str(legacy_root / "dist_cache.sqlite")

    return str((shared_root / "dist_cache.sqlite").resolve())


DB_DEFAULT = _resolve_default_db_path()


def _now_ts() -> float:
    return time.time()


def _coords_hash(lat: float, lon: float, ndigits: int = 6) -> str:
    # 1e-6度 ≒ 0.11m（lat）/ ≒ 0.11m*cos(lat)（lon）。実用上十分。
    s = f"{round(float(lat), ndigits):.{ndigits}f},{round(float(lon), ndigits):.{ndigits}f}"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _is_db_corrupted(db_path: str) -> bool:
    """データベースファイルの破損チェック"""
    if not os.path.exists(db_path):
        return False
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        result = cur.fetchone()
        conn.close()
        return result[0] != "ok"
    except sqlite3.DatabaseError:
        return True
    except Exception:
        return True


def _recover_db(db_path: str) -> bool:
    """破損したデータベースの修復を試行"""
    backup_path = f"{db_path}.backup_{int(_now_ts())}"
    recovered_path = f"{db_path}.recovered"

    try:
        # 元ファイルをバックアップ
        if os.path.exists(db_path):
            os.rename(db_path, backup_path)

        # .recoverコマンドで修復試行
        import subprocess
        result = subprocess.run(
            ["sqlite3", backup_path, ".recover"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout:
            # 修復データから新しいDBを作成
            conn = sqlite3.connect(recovered_path)
            conn.executescript(result.stdout)
            conn.close()

            # 修復されたファイルを元の場所に配置
            os.rename(recovered_path, db_path)
            print(f"Database recovered successfully. Backup: {backup_path}")
            return True
        else:
            # 修復失敗 - 元ファイルを削除して新規作成
            if os.path.exists(backup_path):
                os.remove(backup_path)
            print(f"Database recovery failed. Creating new database: {db_path}")
            return False

    except Exception as e:
        # 修復失敗 - クリーンアップして新規作成
        for path in [recovered_path, backup_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        print(f"Database recovery error: {e}. Creating new database: {db_path}")
        return False


def ensure_db(db_path: str = DB_DEFAULT) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 破損チェックと自動修復
    if os.path.exists(db_path) and _is_db_corrupted(db_path):
        print(f"Corrupted database detected: {db_path}")
        if not _recover_db(db_path):
            # 修復失敗時は削除して新規作成
            if os.path.exists(db_path):
                os.remove(db_path)

    try:
        conn = sqlite3.connect(db_path, timeout=60.0, isolation_level=None)  # autocommit mode
        cur = conn.cursor()
        # WAL + パフォーマンス設定（安全と速度のバランス）
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA temp_store=MEMORY;")
    except sqlite3.DatabaseError as e:
        # 接続時のエラーも破損として扱う
        print(f"Database connection failed: {e}")
        if os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path, timeout=60.0, isolation_level=None)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA temp_store=MEMORY;")

    # スキーマ
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            bridge_id      TEXT PRIMARY KEY,
            lat            REAL NOT NULL,
            lon            REAL NOT NULL,
            name           TEXT,
            admin          TEXT,
            prefecture     TEXT,
            coords_hash    TEXT NOT NULL,
            updated_at     REAL NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS distances (
            a              TEXT NOT NULL,
            b              TEXT NOT NULL,
            metric         TEXT NOT NULL,
            value          REAL NOT NULL,
            units          TEXT NOT NULL,
            method         TEXT NOT NULL,
            coords_hash_a  TEXT NOT NULL,
            coords_hash_b  TEXT NOT NULL,
            updated_at     REAL NOT NULL,
            PRIMARY KEY (a,b,metric,coords_hash_a,coords_hash_b)
        );
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_nodes_hash ON nodes(coords_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dist_a_metric ON distances(a, metric);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dist_b_metric ON distances(b, metric);")
    return conn


def upsert_nodes(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]]) -> int:
    """rows: dict 反復（bridge_id, lat, lon, [name, admin, prefecture]）"""
    ts = _now_ts()
    cur = conn.cursor()
    cur.execute("BEGIN;")
    cnt = 0
    try:
        for r in rows:
            bid = str(r["bridge_id"])  # required
            lat = float(r["lat"])      # required
            lon = float(r["lon"])      # required
            name = r.get("name")
            admin = r.get("admin")
            pref = r.get("prefecture")
            ch = _coords_hash(lat, lon)
            cur.execute(
                """
                INSERT INTO nodes(bridge_id,lat,lon,name,admin,prefecture,coords_hash,updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(bridge_id) DO UPDATE SET
                    lat=excluded.lat, lon=excluded.lon,
                    name=excluded.name, admin=excluded.admin, prefecture=excluded.prefecture,
                    coords_hash=excluded.coords_hash, updated_at=excluded.updated_at
                ;
                """,
                (bid, lat, lon, name, admin, pref, ch, ts),
            )
            cnt += 1
        cur.execute("COMMIT;")
    except Exception:
        cur.execute("ROLLBACK;")
        raise
    return cnt


def get_coords(conn: sqlite3.Connection, ids: Sequence[str]) -> Dict[str, Tuple[float, float, str]]:
    if not ids:
        return {}
    cur = conn.cursor()
    out: Dict[str, Tuple[float, float, str]] = {}
    # IN 句制限回避（SQLITE_MAX_VARIABLE_NUMBER ≈ 999）
    chunk = 800
    for i in range(0, len(ids), chunk):
        sub = ids[i : i + chunk]
        qmarks = ",".join(["?"] * len(sub))
        cur.execute(
            f"SELECT bridge_id, lat, lon, coords_hash FROM nodes WHERE bridge_id IN ({qmarks});",
            tuple(sub),
        )
        for bid, lat, lon, ch in cur.fetchall():
            out[bid] = (float(lat), float(lon), str(ch))
    return out


def _canonical_pair(a: str, b: str) -> Tuple[str, str]:
    return (a, b) if a < b else (b, a)


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    R = 6371.0088  # km
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.minimum(1, np.sqrt(a)))
    return R * c


def get_or_compute_pairs(
    conn: sqlite3.Connection,
    pairs: Iterable[Tuple[str, str]],
    metric: str = "haversine_km",
    batch_size: int = 5000,
) -> List[Tuple[str, str, float]]:
    pairs = [
        _canonical_pair(str(a), str(b)) for (a, b) in pairs if a != b
    ]
    if not pairs:
        return []

    ids = sorted({x for ab in pairs for x in ab})
    coords = get_coords(conn, ids)

    # 既存距離の個別照会（堅牢だが多数の場合は遅い → 将来最適化）
    cur = conn.cursor()
    hit_vals: Dict[Tuple[str, str, str, str], float] = {}
    for a, b in pairs:
        ca = coords.get(a)
        cb = coords.get(b)
        if not ca or not cb:
            continue
        ch_a = ca[2]
        ch_b = cb[2]
        cur.execute(
            """
            SELECT value FROM distances
            WHERE a=? AND b=? AND metric=? AND coords_hash_a=? AND coords_hash_b=?
            ;
            """,
            (a, b, metric, ch_a, ch_b),
        )
        row = cur.fetchone()
        if row is not None:
            hit_vals[(a, b, ch_a, ch_b)] = float(row[0])

    miss: List[Tuple[str, str]] = []
    for a, b in pairs:
        ca = coords.get(a)
        cb = coords.get(b)
        if not ca or not cb:
            continue
        key = (a, b, ca[2], cb[2])
        if key not in hit_vals:
            miss.append((a, b))

    results: List[Tuple[str, str, float]] = []
    results.extend([(a, b, v) for (a, b, ch_a, ch_b), v in hit_vals.items()])

    if not miss:
        return results

    # 未計算分をバッチで計算 → INSERT
    ts = _now_ts()
    units = "km"
    method = "haversine"
    for i in range(0, len(miss), batch_size):
        sub = miss[i : i + batch_size]
        la = np.array([coords[a][0] for a, b in sub], dtype=np.float64)
        lo = np.array([coords[a][1] for a, b in sub], dtype=np.float64)
        lb = np.array([coords[b][0] for a, b in sub], dtype=np.float64)
        lob = np.array([coords[b][1] for a, b in sub], dtype=np.float64)
        dist = haversine_km(la, lo, lb, lob)

        rows = []
        for (a, b), d in zip(sub, dist.tolist()):
            ch_a = coords[a][2]
            ch_b = coords[b][2]
            rows.append((a, b, metric, float(d), units, method, ch_a, ch_b, ts))

        cur.execute("BEGIN;")
        try:
            cur.executemany(
                """
                INSERT OR REPLACE INTO distances
                (a,b,metric,value,units,method,coords_hash_a,coords_hash_b,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?);
                """,
                rows,
            )
            cur.execute("COMMIT;")
        except Exception:
            cur.execute("ROLLBACK;")
            raise

        results.extend([(a, b, v) for (a, b, _, v, *_rest) in [(r[0], r[1], r[2], r[3], None) for r in rows]])

    return results


def get_distance_matrix(
    conn: sqlite3.Connection, ids: Sequence[str], metric: str = "haversine_km"
) -> Tuple[np.ndarray, List[str]]:
    ids = [str(x) for x in ids]
    n = len(ids)
    if n == 0:
        return np.zeros((0, 0), dtype=np.float64), []

    # 全組ペア（i<j）
    pairs = [(ids[i], ids[j]) for i in range(n) for j in range(i + 1, n)]
    total_pairs = len(pairs)

    # キャッシュヒット数をチェック
    coords = get_coords(conn, ids)
    cur = conn.cursor()
    cache_hit_count = 0

    for a, b in pairs:
        ca = coords.get(a)
        cb = coords.get(b)
        if not ca or not cb:
            continue
        ch_a = ca[2]
        ch_b = cb[2]
        cur.execute(
            """
            SELECT 1 FROM distances
            WHERE a=? AND b=? AND metric=? AND coords_hash_a=? AND coords_hash_b=?
            LIMIT 1;
            """,
            (a, b, metric, ch_a, ch_b),
        )
        if cur.fetchone() is not None:
            cache_hit_count += 1

    missing_count = total_pairs - cache_hit_count
    print(f"[距離キャッシュ] 総ペア数: {total_pairs:,}件, キャッシュヒット: {cache_hit_count:,}件, 未計算: {missing_count:,}件")

    if missing_count > 0:
        print(f"[距離キャッシュ] {missing_count:,}件の距離を新規計算します...")

    res = get_or_compute_pairs(conn, pairs, metric=metric)

    # 行列化
    idx = {bid: i for i, bid in enumerate(ids)}
    mat = np.zeros((n, n), dtype=np.float64)
    for a, b, v in res:
        i = idx[a]
        j = idx[b]
        mat[i, j] = v
        mat[j, i] = v
    # 対角は0
    return mat, ids


def get_edges_within(
    conn: sqlite3.Connection, ids: Sequence[str], D_km: float, metric: str = "haversine_km"
) -> List[Tuple[str, str, float]]:
    """指定ID群のうち、距離がD_km以下のエッジを返す（キャッシュ更新も行う）。"""
    ids = [str(x) for x in ids]
    pairs = [(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))]
    res = get_or_compute_pairs(conn, pairs, metric=metric)
    return [(a, b, v) for (a, b, v) in res if v <= D_km]


# 直接実行時の簡易デモ
if __name__ == "__main__":
    conn = ensure_db()
    # サンプルノード
    sample = [
        {"bridge_id": f"B{i}", "lat": 38.2 + i * 0.01, "lon": 140.9 + i * 0.01}
        for i in range(5)
    ]
    upsert_nodes(conn, sample)
    mat, order = get_distance_matrix(conn, [s["bridge_id"] for s in sample])
    print("order:", order)
    print("matrix (km):\n", np.round(mat, 3))
