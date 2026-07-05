# -*- coding: utf-8 -*-
"""共通可視化ユーティリティ。

`20251206.ipynb` の cell 6, 10, 34, 41 でほぼ同一の日本語フォント設定が
4回コピペされていた問題（`notes/pre_git_migration_inventory.md` 7-2章-3）を
解消するための共通関数。
"""

from __future__ import annotations

PREFERRED_JAPANESE_FONTS = [
    "Hiragino Sans",
    "Yu Gothic",
    "Meiryo",
    "Noto Sans CJK JP",
    "IPAexGothic",
    "IPAPGothic",
    "VL PGothic",
    "TakaoGothic",
    "DejaVu Sans",
]


def setup_japanese_font(preferred: list[str] | None = None) -> str:
    """利用可能な日本語フォントを選び matplotlib に設定して名前を返す。"""
    import matplotlib
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    candidates = preferred if preferred is not None else PREFERRED_JAPANESE_FONTS
    available = {f.name for f in fm.fontManager.ttflist}
    selected = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["font.family"] = selected
    # ベクタ形式（PDF/EPS）でフォントを埋め込み可能にする（cell 26 由来）
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    return selected
