# -*- coding: utf-8 -*-
"""STEP3-2: 6市町村フィルタ（N=322 の決定ロジック）。

`20251206.ipynb` cell 25 の再現。宮城県RC橋から、対象6市町村
（七ヶ宿町、白石市、蔵王町、川崎町、村田町、大河原町）が管理者の
橋梁だけを抽出する。期待される件数は **322件**
（判定 I=104, II=209, III=8, IV=0, その他=1。
notes/pre_git_migration_inventory.md 0-1章で確定）。

使用例:
    python scripts/step3_filter_target_municipalities.py \
        --input data/processed/miyagi_rc_bridges.csv \
        --output data/processed/target_rc_bridges_322.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

#: 対象6市町村（N=322 の根拠。cell 25 の target_admins と同一）
TARGET_ADMINS = ["七ヶ宿町", "白石市", "蔵王町", "川崎町", "村田町", "大河原町"]

#: 期待される抽出件数
EXPECTED_COUNT = 322


def filter_target_municipalities(
    df_rc: pd.DataFrame, target_admins: list[str] | None = None
) -> pd.DataFrame:
    """管理者が対象市町村のいずれかである行を抽出する。"""
    admins = target_admins if target_admins is not None else TARGET_ADMINS
    if "管理者" not in df_rc.columns:
        raise RuntimeError("入力に管理者列がありません。step3_extract_rc_bridges.py の出力を渡してください。")
    return df_rc[df_rc["管理者"].isin(admins)].reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="RC橋CSV（step3_extract_rc_bridges.py の出力）")
    parser.add_argument("--output", required=True, help="出力CSVパス")
    args = parser.parse_args()

    df_rc = pd.read_csv(args.input)
    subset = filter_target_municipalities(df_rc)

    counts = subset["判定"].value_counts(dropna=False).to_dict() if "判定" in subset.columns else {}
    print(f"対象6市町村の橋梁数: {len(subset):,} 件（期待値 {EXPECTED_COUNT}）")
    print("判定内訳:", {k: counts.get(k, 0) for k in [1, 2, 3, 4]},
          "その他:", sum(v for k, v in counts.items() if k not in [1, 2, 3, 4]))
    if len(subset) != EXPECTED_COUNT:
        print(f"警告: 件数が期待値 {EXPECTED_COUNT} と一致しません。入力データを確認してください。")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    subset.to_csv(out, index=False)
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
