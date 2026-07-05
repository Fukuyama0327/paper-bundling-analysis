# -*- coding: utf-8 -*-
"""STEP3-3: 道路メンテナンス年報突合結果の読込とeMarkov入力の整形。

`20251206.ipynb` cell 13（施設番号突合）、cell 15（供用開始時点 times=0 の追加）、
cell 17（eMarkov入力整形）をグローバル変数依存なしで再実装。

入力:
  - RC橋CSV（step3_extract_rc_bridges.py の出力。施設番号・架設年度列を使用）
  - 施設番号付与済み道路メンテナンス年報CSV（ステップ2の出力、
    例: 04_宮城県.csv。matched_shisetsu_bangou 列必須）

出力: eMarkov入力TSV（before, after, interval 列）をシナリオ別に4種
  - markov_input_without_supply.txt
  - markov_input_without_supply_collapse.txt
  - markov_input_with_supply.txt          （中間審査pptxの採用系列）
  - markov_input_with_supply_collapse.txt （20251207_200558 実行の採用系列）

使用例:
    python scripts/step3_prepare_markov_input.py \
        --rc-bridges data/processed/miyagi_rc_bridges.csv \
        --maintenance data/external/maintenance_prefecture_exports_with_shisetsu/04_宮城県.csv \
        --output-dir data/processed/markov_input
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.preprocessing import (
    convert_era_to_western,
    hantei_to_int,
    normalize_hantei_to_roman,
    normalize_supply_year,
)

MAX_INSPECTION_INTERVAL = 30  # 異常に長い点検間隔の閾値（年、cell 17）


def build_matched_history(df_rc: pd.DataFrame, maint_df: pd.DataFrame) -> pd.DataFrame:
    """RC橋の施設番号と道路メンテナンス年報を突合し点検履歴を作る（cell 13）。"""
    if "matched_shisetsu_bangou" not in maint_df.columns:
        raise RuntimeError("道路メンテナンス年報CSVに matched_shisetsu_bangou 列がありません。")

    rc_ids = (
        df_rc["施設番号"].astype(str).str.strip().str.upper().replace("", pd.NA).dropna()
    )
    rc_id_set = set(rc_ids)

    work = maint_df[maint_df["matched_shisetsu_bangou"].astype(str).str.strip() != ""].copy()
    work["matched_shisetsu_bangou"] = work["matched_shisetsu_bangou"].str.split(r"\s*\|\s*")
    work = work.explode("matched_shisetsu_bangou")
    work["matched_shisetsu_bangou"] = work["matched_shisetsu_bangou"].astype(str).str.strip()
    work = work[work["matched_shisetsu_bangou"] != ""]
    work["matched_shisetsu_bangou_upper"] = work["matched_shisetsu_bangou"].str.upper()
    work = work[work["matched_shisetsu_bangou_upper"].isin(rc_id_set)].copy()
    if work.empty:
        raise RuntimeError("RC橋に一致する matched_shisetsu_bangou が見つかりませんでした。")

    year_col = "fiscal_year" if "fiscal_year" in work.columns else "tenken_nendo"
    if year_col not in work.columns:
        work[year_col] = ""
    work["fiscal_year_converted"] = work[year_col].apply(convert_era_to_western)
    work["fiscal_year_numeric"] = pd.to_numeric(work["fiscal_year_converted"], errors="coerce")
    if "hantei" not in work.columns:
        work["hantei"] = ""
    work["match"] = pd.factorize(work["matched_shisetsu_bangou"])[0] + 1
    work = work.sort_values(
        ["match", "fiscal_year_numeric", "matched_shisetsu_bangou"]
    ).reset_index(drop=True)
    work["times"] = work.groupby("match").cumcount() + 1

    history = work[
        ["matched_shisetsu_bangou", "fiscal_year_converted", "hantei", "match", "times"]
    ].rename(columns={"fiscal_year_converted": "fiscal_year"})
    history["fiscal_year"] = history["fiscal_year"].replace({"": pd.NA})
    return history


def clean_history(history: pd.DataFrame) -> pd.DataFrame:
    """判定の正規化と match×times 重複除去（cell 15 前半）。"""
    work = history.copy()
    work["hantei"] = work["hantei"].apply(normalize_hantei_to_roman)
    n_invalid = int(work["hantei"].isna().sum())
    if n_invalid:
        print(f"hantei 正規化で {n_invalid:,} 件を除外しました")
    work = work.dropna(subset=["hantei"]).reset_index(drop=True)
    n_dup = int(work.duplicated(subset=["match", "times"], keep="first").sum())
    if n_dup:
        print(f"match×times が重複していた {n_dup:,} 件を除外しました")
    return work.drop_duplicates(subset=["match", "times"], keep="first").reset_index(drop=True)


def add_supply_start_rows(history: pd.DataFrame, df_rc: pd.DataFrame) -> pd.DataFrame:
    """架設年度を times=0（健全度I）として履歴に追加する（cell 15 後半）。"""
    if "架設年度" not in df_rc.columns:
        print("注意: 架設年度列が存在しないため times=0 行は追加されません。")
        return history.copy()

    rc_supply = df_rc[["施設番号", "架設年度"]].dropna(subset=["施設番号", "架設年度"]).copy()
    rc_supply["facility_upper"] = rc_supply["施設番号"].astype(str).str.strip().str.upper()
    rc_supply["supply_year"] = rc_supply["架設年度"].apply(normalize_supply_year)
    rc_supply = rc_supply[rc_supply["facility_upper"] != ""].dropna(subset=["supply_year"])
    if rc_supply.empty:
        print("架設年度情報が得られなかったため times=0 行の追加をスキップしました。")
        return history.copy()

    supply_map = rc_supply.drop_duplicates("facility_upper").set_index("facility_upper")["supply_year"]
    groups, added, skipped = [], 0, 0
    for match_id, group in history.groupby("match", sort=False):
        times1 = group[group["times"] == 1]
        if times1.empty:
            groups.append(group)
            continue
        facility_upper = (
            times1["matched_shisetsu_bangou"].astype(str).str.strip().str.upper().iloc[0]
        )
        start_year = supply_map.get(facility_upper, pd.NA)
        if pd.isna(start_year) or start_year == "":
            groups.append(group)
            skipped += 1
            continue
        new_row = {col: pd.NA for col in group.columns}
        new_row["matched_shisetsu_bangou"] = times1["matched_shisetsu_bangou"].iloc[0]
        new_row["fiscal_year"] = start_year
        new_row["hantei"] = "I"  # 架設時は健全度I（最良）を仮定
        new_row["match"] = match_id
        new_row["times"] = 0
        groups.append(pd.concat([pd.DataFrame([new_row], columns=group.columns), group], ignore_index=True))
        added += 1
    result = pd.concat(groups, ignore_index=True)
    print(f"times=0 行を {added:,} 件追加しました。（架設年度不明でスキップ: {skipped:,} 件）")
    return result


def prepare_markov_input(
    history_df: pd.DataFrame, label: str, collapse_iv: bool = False
) -> pd.DataFrame:
    """履歴 DataFrame から eMarkov 入力（before/after/interval）を整形する（cell 17）。"""
    if history_df is None or history_df.empty:
        print(f"[{label}] 履歴が空のため処理をスキップします。")
        return pd.DataFrame()

    work = history_df.copy()
    if collapse_iv:
        collapse_map = {"IV": "III", "Ⅳ": "III", "4": "III", "４": "III", "4.0": "III"}
        work["hantei"] = work["hantei"].astype(str).str.strip().str.upper().replace(collapse_map)

    src = work.dropna(subset=["matched_shisetsu_bangou"]).copy()
    src["matched_shisetsu_bangou_upper"] = (
        src["matched_shisetsu_bangou"].astype(str).str.strip().str.upper()
    )
    src = src[src["matched_shisetsu_bangou_upper"] != ""]
    src["fiscal_year_numeric"] = pd.to_numeric(src["fiscal_year"], errors="coerce")
    src = src.dropna(subset=["fiscal_year_numeric"])
    src = src.sort_values(["matched_shisetsu_bangou_upper", "match", "times"]).reset_index(drop=True)
    grouped = src.groupby("matched_shisetsu_bangou_upper")
    src["after_hantei"] = grouped["hantei"].shift(-1)
    src["after_year"] = grouped["fiscal_year_numeric"].shift(-1)

    transitions = src.dropna(subset=["after_hantei", "after_year"]).copy()
    transitions["before_numeric"] = transitions["hantei"].apply(hantei_to_int)
    transitions["after_numeric"] = transitions["after_hantei"].apply(hantei_to_int)
    transitions = transitions.dropna(subset=["before_numeric", "after_numeric"])
    transitions["interval"] = (
        transitions["after_year"] - transitions["fiscal_year_numeric"]
    ).astype("Int64")
    transitions = transitions[transitions["interval"] > 0]
    transitions["after_minus_before"] = (
        transitions["after_numeric"] - transitions["before_numeric"]
    ).astype("Int64")

    markov_input = transitions[
        ["matched_shisetsu_bangou", "hantei", "after_hantei", "interval", "after_minus_before"]
    ].rename(columns={"hantei": "before", "after_hantei": "after"})

    n_negative = int((markov_input["after_minus_before"] < 0).sum())
    if n_negative:
        print(f"[{label}] after-before が負（改善）の行 {n_negative:,} 件を除外します")
    markov_input = markov_input[markov_input["after_minus_before"] >= 0].copy()

    n_long = int((markov_input["interval"] > MAX_INSPECTION_INTERVAL).sum())
    if n_long:
        print(f"[{label}] interval > {MAX_INSPECTION_INTERVAL} の行 {n_long:,} 件を除外します")
    markov_input = markov_input[markov_input["interval"] <= MAX_INSPECTION_INTERVAL]

    markov_input = markov_input[
        ["matched_shisetsu_bangou", "before", "after", "interval", "after_minus_before"]
    ].reset_index(drop=True)
    print(f"[{label}] フィルタ後の行数: {len(markov_input):,}")
    return markov_input


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rc-bridges", required=True, help="RC橋CSV")
    parser.add_argument("--maintenance", required=True, help="施設番号付与済み道路メンテナンス年報CSV")
    parser.add_argument("--output-dir", required=True, help="eMarkov入力TSVの出力ディレクトリ")
    args = parser.parse_args()

    df_rc = pd.read_csv(args.rc_bridges, dtype={"施設番号": str})
    df_rc["施設番号"] = df_rc["施設番号"].fillna("").astype(str).str.strip()
    maint_df = pd.read_csv(args.maintenance, dtype=str).fillna("")

    history = clean_history(build_matched_history(df_rc, maint_df))
    print(f"履歴総数: {len(history):,} / マッチ橋梁数: {history['match'].nunique():,}")
    history_with_supply = add_supply_start_rows(history, df_rc)

    scenarios = {
        "without_supply": (history, False),
        "without_supply_collapse": (history, True),
        "with_supply": (history_with_supply, False),
        "with_supply_collapse": (history_with_supply, True),
    }
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, (hist, collapse) in scenarios.items():
        markov_input = prepare_markov_input(hist, key, collapse_iv=collapse)
        if markov_input.empty:
            continue
        path = out_dir / f"markov_input_{key}.txt"
        markov_input.to_csv(path, index=False, sep="\t", encoding="utf-8-sig")
        print(f"保存: {path}")


if __name__ == "__main__":
    main()
