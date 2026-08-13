# -*- coding: utf-8 -*-
"""本文が読む図が、投稿に耐える形式で埋め込まれているかを確かめる。

matplotlib は既定で PDF 内の文字を **Type 3 フォント**として埋め込む。
Type 3 は文字を図形として持つため、文字として検索・抽出できず、
ASCE をはじめ多くの学術誌が投稿規定で受け付けない。
``plotting_utils.setup_figure_defaults()`` を通せば TrueType（Type 0/TrueType）
で埋め込まれるので、それが全図に効いているかをここで検査する。

失敗したときは、作図スクリプトが setup_figure_defaults() を呼んでいるかを確認し、
図を作り直すこと（notebooks/pipeline_walkthrough.ipynb 第6章）。
"""

from __future__ import annotations

import re
import zlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_TEX = REPO_ROOT / "paper/latex/main.tex"
FIGURES = REPO_ROOT / "figures"

FONT_SUBTYPE = re.compile(rb"/Subtype\s*/(Type1|Type3|TrueType|Type0)")


def embedded_font_types(pdf_path: Path) -> set[str]:
    """PDF に埋め込まれたフォントの Subtype を集める（圧縮ストリーム内も見る）。"""
    data = pdf_path.read_bytes()
    kinds = set(FONT_SUBTYPE.findall(data))
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            kinds |= set(FONT_SUBTYPE.findall(zlib.decompress(match.group(1))))
        except zlib.error:
            continue
    return {kind.decode() for kind in kinds}


def referenced_figures() -> list[str]:
    """main.tex が \\includegraphics で参照しているパスを返す。"""
    if not MAIN_TEX.exists():
        return []
    tex = MAIN_TEX.read_text(encoding="utf-8")
    return re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)


@pytest.mark.parametrize("ref", referenced_figures())
def test_paper_figure_has_no_type3_font(ref: str) -> None:
    """本文が読む図に Type 3 フォントが混じっていないこと。"""
    source = FIGURES / Path(ref).name
    if source.suffix.lower() != ".pdf":
        pytest.skip(f"ベクタ形式ではない参照: {ref}")
    if not source.exists():
        pytest.skip(f"生成物が無い: {source}")
    kinds = embedded_font_types(source)
    assert "Type3" not in kinds, (
        f"{source.name} に Type 3 フォントが含まれる（検出: {sorted(kinds)}）。"
        " 作図スクリプトが setup_figure_defaults() を呼んでいるか確認し、図を作り直すこと。"
    )


def test_main_tex_uses_vector_figures() -> None:
    """本文の図がベクタ形式（PDF）で参照されていること。"""
    refs = referenced_figures()
    if not refs:
        pytest.skip("main.tex が無い")
    raster = [r for r in refs if Path(r).suffix.lower() in (".png", ".jpg", ".jpeg")]
    assert not raster, f"ラスタ形式で参照されている図がある: {raster}"
