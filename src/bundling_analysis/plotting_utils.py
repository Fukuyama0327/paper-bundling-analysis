# -*- coding: utf-8 -*-
"""共通可視化ユーティリティ。

`20251206.ipynb` の cell 6, 10, 34, 41 でほぼ同一の日本語フォント設定が
4回コピペされていた問題（`notes/pre_git_migration_inventory.md` 7-2章-3）を
解消するための共通関数。
"""

from __future__ import annotations

import warnings
from pathlib import Path

#: 論文の図に使う書体。本文（Times系）に合わせる。matplotlib同梱ではないので、
#: 無い環境では下位の候補へ落ちる（そのときは setup_figure_defaults が警告する）。
FIGURE_FONT_CANDIDATES = ("Times New Roman", "Nimbus Roman", "DejaVu Serif")
FIGURE_FONT_FAMILY = "serif"

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

#: 本文の版面幅。``paper/latex/ascelike-new.cls`` が組む \textwidth = 469.755 pt を
#: インチへ直した値（1 in = 72.27 pt）。図を「本文に置いたときの実寸」で作るために使う。
TEXT_WIDTH_PT = 469.755
TEXT_WIDTH_IN = TEXT_WIDTH_PT / 72.27

#: 図中の文字の大きさ [pt]。図を実寸で作るので、この値がそのまま誌面での大きさになる。
FIGURE_FONT_SIZE = 10.5


def figure_width(fraction: float = 1.0) -> float:
    """``\includegraphics[width=<fraction>\linewidth]`` に等倍で収まる図の横幅 [in]。

    図ごとに figsize と配置幅がばらばらだと、同じ 10 pt で書いた文字が誌面では
    4 pt から 8 pt までばらつく（2026-09-25 の査読コメント「全ての図でのフォントを
    統一してほしい」）。作図側を誌面の実寸に合わせ、``\includegraphics`` の倍率を
    1.0 に固定すれば、この食い違いは原理的に起きない。

    本文側の ``width=0.82\linewidth`` に対しては ``figure_width(0.82)`` を渡す。
    """
    if not 0 < fraction <= 1:
        raise ValueError(f"fraction は 0 < f <= 1 の範囲で指定する: {fraction}")
    return TEXT_WIDTH_IN * fraction


def figure_size(fraction: float = 1.0, aspect: float = 0.62) -> tuple[float, float]:
    """``figure_width`` の横幅と、``aspect`` 倍の高さからなる figsize を返す。"""
    width = figure_width(fraction)
    return (width, width * aspect)


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

    あわせて出力を決定的にする。matplotlib は PDF に生成時刻（``/CreationDate``）を
    埋めるため、内容が同じでも実行のたびにバイト列が変わり、図の同期確認（md5比較）や
    gitの差分が「中身は同じなのに変わった」と鳴り続ける。``SOURCE_DATE_EPOCH`` が
    設定されていればその時刻が使われるので、未設定のときだけ固定値を入れる
    （再現可能ビルドの慣行に従う）。SVGは要素IDに乱数が入るため完全一致にはならない。

    論文の図を出力するスクリプトは、保存の前にこれを呼ぶこと。
    実際に解決された書体名を返す。
    """
    import os

    import matplotlib

    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1000000000")

    # 書体を明示的に指定する。個人設定（~/.matplotlib/matplotlibrc）が
    # font.sans-serif に環境固有の書体を指定していると、それが図に埋め込まれるため。
    # 実際、macOS で作った図には Hiragino Sans が埋め込まれ、Windows の
    # Adobe Acrobat で文字化けするという報告があった（2026-09-06）。
    #
    # Hiragino は .ttc の CJK 書体で、サブセット化のときに
    # 「meta NOT subset; don't know how to subset; dropped」が出る。
    # Times New Roman や Arial では同じ警告は出ず、埋め込みも問題ない。
    # 本文の書体に合わせて Times New Roman を第一候補とする。
    matplotlib.rcParams["font.family"] = FIGURE_FONT_FAMILY
    matplotlib.rcParams["font.serif"] = list(FIGURE_FONT_CANDIDATES)
    matplotlib.rcParams["mathtext.fontset"] = "stix"   # Times に近い数式書体
    matplotlib.rcParams["axes.unicode_minus"] = False

    # 文字の大きさも固定する。図は figure_size() で誌面の実寸に作るので、
    # ここで決めた pt がそのまま誌面での大きさになり、図をまたいで揃う。
    matplotlib.rcParams["font.size"] = FIGURE_FONT_SIZE
    matplotlib.rcParams["axes.labelsize"] = FIGURE_FONT_SIZE
    matplotlib.rcParams["axes.titlesize"] = FIGURE_FONT_SIZE
    matplotlib.rcParams["xtick.labelsize"] = FIGURE_FONT_SIZE - 0.5
    matplotlib.rcParams["ytick.labelsize"] = FIGURE_FONT_SIZE - 0.5
    matplotlib.rcParams["legend.fontsize"] = FIGURE_FONT_SIZE - 0.5

    # 第一候補が無い環境では matplotlib が黙って別の書体に落とす。図の見た目が
    # 環境ごとに変わるのを見逃さないよう、実際に解決された書体を確かめて知らせる。
    resolved = _resolved_font_name()
    if resolved != FIGURE_FONT_CANDIDATES[0]:
        warnings.warn(
            f"図の書体が {FIGURE_FONT_CANDIDATES[0]} ではなく {resolved} になった。"
            f" この環境で作った図は他の環境と字形が変わる。"
            f" 候補: {list(FIGURE_FONT_CANDIDATES)}",
            stacklevel=2,
        )
    return resolved


def _resolved_font_name() -> str:
    """実際に使われる書体のファミリ名を返す。"""
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties, findfont, get_font

    path = findfont(FontProperties(family=plt.rcParams["font.family"]))
    try:
        return get_font(path).family_name
    except Exception:
        return Path(path).stem


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
