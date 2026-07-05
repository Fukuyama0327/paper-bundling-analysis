# -*- coding: utf-8 -*-
"""STEP3-1: x-Road原データから宮城県RC橋を抽出する。

`20251206.ipynb` cell 4, 8, 9 のロジックをグローバル変数依存なしで再実装。

入力: 77条調査（x-Road）原データCSV（例: prefecture_04_宮城県_12425records_original.csv）
出力: RC橋のみのCSV（緯度・経度・判定・管理者・施設番号等の正規化列付き）

期待される件数（notes/pre_git_migration_inventory.md 0-1章）: 宮城県RC橋 5,525件

使用例:
    python scripts/step3_extract_rc_bridges.py \
        --input data/external/prefecture_04_宮城県_12425records_original.csv \
        --output data/processed/miyagi_rc_bridges.csv \
        [--boundary data/N03-20230101_GML/N03-23_230101.shp]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.preprocessing import (
    extract_hundred_digit,
    normalize_hantei,
    parse_latlon,
)

#: 読み込む主要列（cell 4 の WANT リスト）
WANTED_COLUMNS = [
    "shisetsu_id",
    "tenken.kiroku.hantei_kubun",
    "syogen.gyousei_kuiki.todoufuken_mei",
    "syogen.gyousei_kuiki.shikuchouson_mei",
    "syogen.shisetsu.meisyou",
    "syogen.rosen.meisyou",
    "syogen.kanrisya.meisyou",
    "syogen.kouzou_keishiki.joubu",
    "syogen.kasetsu_nendo",
    "shisetsu_bangou",
]

RENAME_MAP = {
    "syogen.kasetsu_nendo": "架設年度",
    "syogen.shisetsu.meisyou": "橋名",
    "syogen.rosen.meisyou": "路線",
    "syogen.gyousei_kuiki.shikuchouson_mei": "市区町村",
    "syogen.kanrisya.meisyou": "管理者",
    "syogen.kouzou_keishiki.joubu": "構造上部",
}


def load_xroad_prefecture(
    input_path: str | Path,
    prefecture: str = "宮城県",
    chunksize: int = 200_000,
) -> pd.DataFrame:
    """x-Road原データを読み込み、対象都道府県・座標正常の行に絞る（cell 4）。"""
    input_path = str(input_path)
    header = pd.read_csv(input_path, nrows=0).columns.tolist()
    usecols = [c for c in WANTED_COLUMNS if c in header]
    if not {"shisetsu_id", "tenken.kiroku.hantei_kubun"}.issubset(usecols):
        raise RuntimeError("必要列（shisetsu_id, tenken.kiroku.hantei_kubun）が見つかりません。")

    frames = []
    for chunk in pd.read_csv(input_path, usecols=usecols, chunksize=chunksize):
        sub = chunk.copy()
        if "syogen.gyousei_kuiki.todoufuken_mei" in sub.columns:
            sub = sub[sub["syogen.gyousei_kuiki.todoufuken_mei"] == prefecture]
            if sub.empty:
                continue
        latlon = sub["shisetsu_id"].apply(parse_latlon)
        sub["緯度"] = latlon.apply(lambda t: t[0])
        sub["経度"] = latlon.apply(lambda t: t[1])
        sub["判定"] = sub["tenken.kiroku.hantei_kubun"].apply(normalize_hantei)
        sub = sub[(sub["緯度"].between(20, 46)) & (sub["経度"].between(122, 154))]
        if not sub.empty:
            frames.append(sub)
    if not frames:
        raise RuntimeError(f"{prefecture} の有効レコードが取得できませんでした。")

    df = pd.concat(frames, ignore_index=True)
    for src, dst in RENAME_MAP.items():
        df[dst] = df.get(src)
    if "shisetsu_bangou" in df.columns:
        df["施設番号"] = df["shisetsu_bangou"].fillna("").astype(str).str.strip()
    else:
        df["施設番号"] = ""
    return df


def extract_rc_bridges(df: pd.DataFrame) -> pd.DataFrame:
    """構造区分コードの百の位=3（RC）で抽出する（cell 8）。"""
    src_col = "syogen.kouzou_keishiki.joubu"
    if src_col not in df.columns:
        raise RuntimeError(f"構造上部列（{src_col}）が見当たりません。")
    df = df.copy()
    df["構造上部_百の位"] = df[src_col].apply(extract_hundred_digit)
    return df[df["構造上部_百の位"] == 3].reset_index(drop=True)


def add_kenzendo_column(df: pd.DataFrame) -> pd.DataFrame:
    """判定列から健全度列（IV→IIIに折り畳み）を生成する（cell 9 末尾）。"""
    df = df.copy()
    if "健全度" not in df.columns and "判定" in df.columns:
        df["健全度"] = df["判定"].apply(
            lambda x: min(int(x), 3) if pd.notna(x) and str(x).isdigit() else 1
        )
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="x-Road原データCSV")
    parser.add_argument("--output", required=True, help="出力CSVパス")
    parser.add_argument("--prefecture", default="宮城県")
    parser.add_argument(
        "--boundary",
        default=None,
        help="行政界シェープファイル（指定時は県境界外の橋梁を除外）",
    )
    args = parser.parse_args()

    df = load_xroad_prefecture(args.input, prefecture=args.prefecture)
    print(f"{args.prefecture} 抽出: {len(df):,} 件（緯度経度あり＆範囲内）")

    df_rc = extract_rc_bridges(df)
    print(f"RC橋抽出: {len(df_rc):,} 件")

    if args.boundary:
        from bundling_analysis.admin_boundary import filter_points_within, load_admin_boundary

        boundary = load_admin_boundary(args.boundary, prefecture=args.prefecture)
        if boundary is not None:
            df_rc, removed = filter_points_within(df_rc, boundary)
            print(f"行政界チェック: {removed} 件除外 → {len(df_rc):,} 件")

    df_rc = add_kenzendo_column(df_rc)
    counts = df_rc["判定"].value_counts(dropna=False).to_dict()
    print("判定内訳:", {k: counts.get(k, 0) for k in [1, 2, 3, 4]},
          "その他:", sum(v for k, v in counts.items() if k not in [1, 2, 3, 4]))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df_rc.to_csv(out, index=False)
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
