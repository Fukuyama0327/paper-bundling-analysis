# -*- coding: utf-8 -*-
"""共通可視化ユーティリティ。

`20251206.ipynb` の cell 6, 10, 34, 41 でほぼ同一の日本語フォント設定が
4回コピペされていた問題（`notes/pre_git_migration_inventory.md` 7-2章-3）を
解消するための共通関数。
"""

from __future__ import annotations

#: 地域数 M ごとの色。同じ M が図をまたいで同じ色になるよう、
#: M を凡例に使う図はすべてここを参照する（`plot_dm_sensitivity.py`,
#: `plot_pareto_radius.py`）。
M_COLORS = {
    1: "#6b7280",
    2: "#4c6fb1",
    3: "#238b8e",
    4: "#cc6c3b",
    5: "#7a4e9e",
    6: "#b0435b",
}

#: 地域数 M ごとのマーカー形状。色だけで区別すると、R(x*) がほぼ同じ位置に
#: 重なった点（例: D=25 の M=3 と M=6）が見分けられないため、形も変える。
M_MARKERS = {
    1: "o",
    2: "s",
    3: "^",
    4: "D",
    5: "v",
    6: "P",
}

#: 形状ごとの見た目の大きさのばらつきを揃えるための倍率。
#: 同じ面積指定でも D（ひし形）や ^（三角）は小さく見える。
M_MARKER_SIZE_SCALE = {
    1: 1.0,
    2: 0.95,
    3: 1.2,
    4: 0.9,
    5: 1.2,
    6: 1.25,
}

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


def setup_figure_defaults() -> None:
    """論文用のベクタ出力（PDF/SVG）の既定を整える。

    matplotlib は既定で PDF・EPS 内の文字を **Type 3 フォント**として埋め込むが、
    ASCE をはじめ多くの学術誌は投稿規定で Type 3 を受け付けない（文字として
    検索・抽出できないため）。``fonttype = 42`` にすると TrueType で埋め込まれる。

    SVG は ``svg.fonttype = "none"`` として文字をパス化せずテキストのまま残す。
    後から書体を差し替えたり、文字を検索したりできる。

    論文の図を出力するスクリプトは、保存の前にこれを呼ぶこと。
    """
    import matplotlib

    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"


def setup_japanese_font(preferred: list[str] | None = None) -> str:
    """利用可能な日本語フォントを選び matplotlib に設定して名前を返す。"""
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    candidates = preferred if preferred is not None else PREFERRED_JAPANESE_FONTS
    available = {f.name for f in fm.fontManager.ttflist}
    selected = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["font.family"] = selected
    # ベクタ形式でフォントを埋め込み可能にする（cell 26 由来）
    setup_figure_defaults()
    return selected
