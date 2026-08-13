# -*- coding: utf-8 -*-
"""tab:transition_counts の生成: 健全度遷移のクロス集計（cell 23 前半）。

markov_input TSVから遷移前×遷移後のクロス集計表を作り、CSVとLaTeX行を出力する。

正本入力: `data/processed/markov_input_20251207_200558/markov_input_with_supply.txt`
（採用推移行列と同一実行のデータ。n=7,628）

経緯: 旧docx/pptxの表（II→II=4,703、計7,638件）は1つ前のデータ状態
（20251207_120512以前）由来で、その後の重複履歴除去でII→IIが10件減った。
main.tex は2026-08-13時点で本スクリプトの出力（II→II=4,693、計7,628件）に
更新済みのため、旧値との差分表示は廃止した。

使用例:
    python scripts/make_transition_counts.py \
        --input data/processed/markov_input_20251207_200558/markov_input_with_supply.txt \
        --output outputs/transition_counts.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.preprocessing import hantei_to_int

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}


def transition_crosstab(markov_input: pd.DataFrame) -> pd.DataFrame:
    """before×after の遷移回数クロス集計（I〜IV）を返す。"""
    before = markov_input["before"].apply(hantei_to_int)
    after = markov_input["after"].apply(hantei_to_int)
    counts = pd.crosstab(before, after).reindex(
        index=[1, 2, 3, 4], columns=[1, 2, 3, 4], fill_value=0
    )
    counts.index = [ROMAN[i] for i in counts.index]
    counts.columns = [ROMAN[i] for i in counts.columns]
    counts.index.name = "Before"
    counts.columns.name = "After"
    return counts


def to_latex_rows(counts: pd.DataFrame) -> str:
    """main.tex の tabular 中身（\\midrule〜\\bottomrule 間の行）を生成する。"""
    lines = []
    for label, row in counts.iterrows():
        cells = " & ".join(str(int(v)) for v in row)
        lines.append(f"{label} & {cells} \\\\")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/markov_input_20251207_200558/markov_input_with_supply.txt"),
        help="markov_input TSV（with_supply系が本文対応）",
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/transition_counts.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep="\t", encoding="utf-8-sig")
    counts = transition_crosstab(df)
    total = int(counts.values.sum())
    print(f"入力: {args.input}（遷移データ {total:,} 件）")
    print(counts.to_string())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.output)
    print(f"保存: {args.output}")
    print("\n--- main.tex 用 LaTeX 行 ---")
    print(to_latex_rows(counts))


if __name__ == "__main__":
    main()
