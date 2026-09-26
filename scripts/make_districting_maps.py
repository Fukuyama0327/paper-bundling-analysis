"""Generate districting maps from a solutions pkl: representative cases + full atlas.

Body-text figures: individual maps for the representative cases (default D=25:M3,
D=40:M1, D=35:M3). Appendix/supplement: an atlas of small-multiple maps for every
(D, M) case in the grid (rows = distance limit D, columns = region count M). Every
case is verified (region sizes + exact objective) against the canonical result grid;
a run metadata JSON records the solutions pkl, git HEAD and verification results.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bundling_analysis.plotting_utils import setup_figure_defaults  # noqa: E402

# 論文用のベクタ出力設定（PDF内の文字をType 3ではなくTrueTypeで埋め込む）。
# 多くの学術誌がType 3を受け付けないため、保存前に必ず適用する。
setup_figure_defaults()

from bundling_analysis.admin_boundary import load_admin_boundaries_gdf  # noqa: E402
from bundling_analysis.districting_map import (  # noqa: E402
    bridge_based_voronoi,
    coords_in_assignment_order,
    load_solutions,
    plot_voronoi_map,
)
from bundling_analysis.expected_contracts import (  # noqa: E402
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)

MUNICIPALITIES = ["白石市", "大河原町", "蔵王町", "村田町", "川崎町", "七ヶ宿町"]


def parse_case(text: str) -> tuple[float, int]:
    d_str, m_str = text.split(":")
    return float(d_str), int(m_str)


def case_counts_and_obj(assignment: np.ndarray, bundle_limit: int, q: float):
    counts = sorted((int(assignment[:, r].sum()) for r in range(assignment.shape[1])), reverse=True)
    obj = sum(expected_contracts(c, bundle_limit, q) for c in counts)
    return counts, obj


def verify(counts, obj, results_df, d, m):
    row = results_df[(results_df["MaxDistance"] == d) & (results_df["M"] == m)]
    if row.empty:
        return None
    exp_counts = sorted((int(x) for x in str(row.iloc[0]["RegionCounts"]).split(";") if x != ""),
                        reverse=True)
    exp_obj = float(row.iloc[0]["ObjectiveValue_Exact"])
    return counts == exp_counts and abs(obj - exp_obj) < 1e-6


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solutions", type=Path, required=True)
    parser.add_argument("--bridges", type=Path,
                        default=Path("data/processed/target_rc_bridges_322.csv"))
    parser.add_argument("--distance-matrix", type=Path,
                        default=Path("data/processed/distance_matrix_322_20251208.pkl"))
    parser.add_argument("--boundary", type=Path,
                        default=Path("data/processed/target_municipalities_boundary.geojson"))
    parser.add_argument("--results-csv", type=Path,
                        default=Path("data/processed/optimization_results_exact_objective.csv"))
    parser.add_argument("--representative", nargs="+", default=["25:3", "30:2", "40:1"],
                        help="本文用の代表ケース（D:M）。2026-08-14に 35:3 を 30:2 へ差し替えた。"
                             "35:3 は地域規模 315/6/1 で、連続性を制約していないため面が分断して見え、"
                             "本文の代表図としては読み取りにくかったことによる（計算は正しい）。")
    parser.add_argument("--bundle-limit", type=int, default=5)
    parser.add_argument("--fig-dir", type=Path, default=Path("figures"))
    parser.add_argument("--atlas-dir", type=Path, default=Path("figures/atlas"))
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    solutions = load_solutions(args.solutions)
    import pickle
    with args.distance_matrix.open("rb") as f:
        order = pickle.load(f)["order"]
    bridges = pd.read_csv(args.bridges)
    coords = coords_in_assignment_order(bridges, order)
    results_df = pd.read_csv(args.results_csv)
    gdf, union = load_admin_boundaries_gdf(args.boundary, municipalities=MUNICIPALITIES)
    bounds = union.bounds if union is not None else None

    verifications: list[dict] = []
    all_ok = True

    def render_case(d, m, ax=None, legend=True):
        assignment = solutions[(d, m)]
        clusters = np.argmax(assignment, axis=1)
        counts, obj = case_counts_and_obj(assignment, args.bundle_limit, q)
        ok = verify(counts, obj, results_df, d, m)
        verifications.append({"D": d, "M": m, "counts": counts, "objective": obj, "verified": ok})
        nonlocal all_ok
        if ok is False:
            all_ok = False
        polys = bridge_based_voronoi(coords, clusters, union)
        # 本文用の図はTeX側にキャプションがあるので図中タイトルを付けない。
        # atlas は36枚を並べるため、どのケースかを示す小さな見出しを残す。
        # 見出しに出す値は地域ごとの f(N_k,L) ではなくその総和、すなわち
        # 目的関数値 Z = sum_k f(N_k, L) なので、本文の記法に合わせて Z と書く。
        title = None if legend else (
            f"D={int(d)}, M={m}\n$Z$={obj:.3f}  ({'/'.join(map(str, counts))})"
        )
        return plot_voronoi_map(polys, coords, clusters, boundary_gdf=gdf, bounds=bounds,
                                title=title, ax=ax, show_legend=legend)

    # --- representative body-text maps ---
    args.fig_dir.mkdir(parents=True, exist_ok=True)
    for text in args.representative:
        d, m = parse_case(text)
        if (d, m) not in solutions:
            print(f"警告: solutions pkl に {text} が無くスキップ")
            continue
        fig, _ = render_case(d, m, legend=True)
        stem = args.fig_dir / f"districting_map_D{int(d)}_M{m}"
        for ext, kw in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
            fig.savefig(stem.with_suffix(f".{ext}"), bbox_inches="tight", **kw)
        plt.close(fig)
        print(f"representative: {stem}.*")

    # --- atlas: rows = D, cols = M ---
    d_values = sorted({d for d, _ in solutions})
    m_values = sorted({m for _, m in solutions})
    fig, axes = plt.subplots(len(d_values), len(m_values),
                             figsize=(2.5 * len(m_values), 2.5 * len(d_values)))
    axes = np.atleast_2d(axes)
    for i, d in enumerate(d_values):
        for j, m in enumerate(m_values):
            ax = axes[i, j]
            if (d, m) in solutions:
                render_case(d, m, ax=ax, legend=False)
                ax.set_title(ax.get_title(), fontsize=10)
            else:
                ax.axis("off")
    # 図上部のキャプションは付けない。説明は TeX 側のキャプションに書く
    # （査読コメント 2026-09-25）。
    fig.tight_layout()   # suptitle を外したので上の余白を空ける必要はない
    args.atlas_dir.mkdir(parents=True, exist_ok=True)
    atlas_stem = args.atlas_dir / "districting_atlas"
    fig.savefig(atlas_stem.with_suffix(".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)

    # atlas はPDFにすると8MB超、SVGは25MB超になるうえ、36枚の一覧を拡大して読む用途でもない。
    # そこでラスタのまま扱う。ただしPNGを uplatex + dvipdfmx で読むには画像サイズを書いた
    # .xbb が要り、その生成（extractbb）は Overleaf のようにシェル実行を禁じた環境では働かない。
    # PNGをPDFに包めば、PDF自身がサイズ情報を持つのでどの環境でも読める（1MB弱に収まる）。
    try:
        from PIL import Image

        with Image.open(atlas_stem.with_suffix(".png")) as image:
            image.convert("RGB").save(atlas_stem.with_suffix(".pdf"), "PDF", resolution=200.0)
        print(f"atlas: {atlas_stem}.png / .pdf（PNGをPDFに包んだもの）")
    except ImportError:
        print(f"atlas: {atlas_stem}.png のみ（Pillow が無くPDF版を作れない。"
              f"本文で読むなら extractbb で .xbb を作ること）")

    meta = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_head": git_head(),
        "solutions": str(args.solutions),
        "bundle_limit": args.bundle_limit,
        "verifications": verifications,
    }
    (args.atlas_dir / "atlas.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    n_ok = sum(1 for v in verifications if v["verified"])
    n_checked = sum(1 for v in verifications if v["verified"] is not None)
    print(f"\n検証: {n_ok}/{n_checked} ケースが結果CSVと一致")
    if not all_ok and not args.no_verify:
        raise SystemExit("検証失敗: 一部ケースが結果CSVと一致しません（--no-verify で無視可）。")


if __name__ == "__main__":
    main()
