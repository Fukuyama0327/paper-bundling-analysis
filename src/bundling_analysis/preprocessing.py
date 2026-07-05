# -*- coding: utf-8 -*-
"""x-Road・道路メンテナンス年報データの正規化ユーティリティ。

`20251208_定期打ち合わせ/20251206.ipynb` の cell 2, 4, 15 に散在していた
補助関数を、グローバル変数に依存しない純粋関数として集約したもの。
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

#: 判定値（ローマ数字・全角・数値表記）→ 整数ステージのマップ
HANTEI_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "Ⅰ": 1, "Ⅱ": 2, "Ⅲ": 3, "Ⅳ": 4, "Ⅴ": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
}


def convert_era_to_western(value: Any) -> str:
    """和暦（"令和3年度" 等）を西暦4桁の文字列へ正規化する（cell 2 由来）。"""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("年度", "").replace("年", "")
    era_map = {"令和": "R", "平成": "H", "昭和": "S", "大正": "T", "明治": "M"}
    for kanji, letter in era_map.items():
        text = text.replace(kanji, letter)
    match = re.match(r"([RHSTM])\s*(\d+)", text)
    if match:
        era = match.group(1)
        year = int(match.group(2))
        offsets = {"M": 1867, "T": 1911, "S": 1925, "H": 1988, "R": 2018}
        base = offsets.get(era)
        if base:
            return str(base + year)
    return re.sub(r"[^0-9]", "", text)


def parse_latlon(value: Any) -> tuple[float, float]:
    """``shisetsu_id`` の "(lat, lon)" 文字列から緯度経度を取り出す（cell 4 由来）。"""
    if pd.isna(value):
        return (float("nan"), float("nan"))
    text = str(value).strip().strip(" \"'()[]")
    parts = [t.strip() for t in text.split(",")]
    if len(parts) != 2:
        return (float("nan"), float("nan"))
    try:
        return float(parts[0]), float(parts[1])
    except Exception:
        return (float("nan"), float("nan"))


def normalize_hantei(value: Any):
    """判定区分を 1〜4 の整数に正規化し、それ以外は 'other' を返す（cell 4 由来）。"""
    try:
        x = int(float(value))
    except Exception:
        return "other"
    return x if x in (1, 2, 3, 4) else "other"


def extract_hundred_digit(code: Any) -> int:
    """構造区分コードの百の位（構造区分、RC=3）を抽出する（cell 4 由来）。"""
    try:
        d = int(float(code)) // 100
        return d if d in (1, 2, 3, 4, 5, 6, 7, 8, 9) else 9
    except Exception:
        return 9


def hantei_to_int(value: Any):
    """判定値を整数ステージへ変換する。変換不能なら ``pd.NA``（cell 17/19 由来）。"""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    if text in HANTEI_MAP:
        return HANTEI_MAP[text]
    try:
        return int(float(text))
    except Exception:
        return pd.NA


def normalize_hantei_to_roman(value: Any):
    """判定値をローマ数字 I〜IV に正規化し、それ以外は ``pd.NA``（cell 15 由来）。"""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    roman_map = {
        "1": "I", "2": "II", "3": "III", "4": "IV",
        "Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV",
    }
    if text in roman_map:
        return roman_map[text]
    if text in {"I", "II", "III", "IV"}:
        return text
    return pd.NA


def normalize_supply_year(value: Any):
    """架設年度を西暦4桁へ正規化し、信頼できない値は ``pd.NA``（cell 15 由来）。"""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    text = text.replace("年度", "").replace("年", "")
    converted = convert_era_to_western(text)
    match = re.search(r"(18|19|20)\d{2}", converted)
    if match:
        return match.group(0)
    try:
        num = int(float(converted))
        if 1800 <= num <= 2100:
            return str(num)
    except ValueError:
        pass
    match = re.search(r"(18|19|20)\d{2}", text)
    if match:
        return match.group(0)
    try:
        num = int(float(text))
        if 1800 <= num <= 2100:
            return str(num)
    except ValueError:
        return pd.NA
    return pd.NA
