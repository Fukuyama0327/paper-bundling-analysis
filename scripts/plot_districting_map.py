"""Render one districting solution (D, M) as a Voronoi + bridge-point map.

Reads a solutions pickle produced by ``run_gurobi_districting.py --solutions-output``
(``{(D, M): {'assignment': 322xM binary, ...}}``; the notebook ``by_distance`` format
is also accepted), aligns the assignment rows to bridge coordinates via the distance
matrix ``order`` <-> ``shisetsu_id``, and draws the regions. The region sizes and exact
objective recomputed from the assignment are verified against the canonical result grid.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

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


def verify_case(assignment: np.ndarray, results_csv: Path, d: float, m: int,
                bundle_limit: int, q: float) -> bool:
    counts = sorted((int(assignment[:, r].sum()) for r in range(assignment.shape[1])), reverse=True)
    obj = sum(expected_contracts(c, bundle_limit, q) for c in counts)
    df = pd.read_csv(results_csv)
    row = df[(df["MaxDistance"] == d) & (df["M"] == m)]
    if row.empty:
        print(f"  警告: 結果CSVに D={d}, M={m} が無く検証をスキップ")
        return True
    exp_counts = sorted((int(x) for x in str(row.iloc[0]["RegionCounts"]).split(";") if x != ""),
                        reverse=True)
    exp_obj = float(row.iloc[0]["ObjectiveValue_Exact"])
    ok = counts == exp_counts and abs(obj - exp_obj) < 1e-6
    print(f"  counts {counts} vs CSV {exp_counts}; obj {obj:.9f} vs {exp_obj:.9f} "
          f"-> {'OK' if ok else 'MISMATCH'}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solutions", type=Path, required=True)
    parser.add_argument("--case", type=parse_case, required=True, help="D:M（例 25:3）")
    parser.add_argument("--bridges", type=Path,
                        default=Path("data/processed/target_rc_bridges_322.csv"))
    parser.add_argument("--distance-matrix", type=Path,
                        default=Path("data/processed/distance_matrix_322_20251208.pkl"))
    parser.add_argument("--boundary", type=Path,
                        default=Path("data/processed/target_municipalities_boundary.geojson"))
    parser.add_argument("--results-csv", type=Path,
                        default=Path("data/processed/optimization_results_exact_objective.csv"))
    parser.add_argument("--bundle-limit", type=int, default=5)
    parser.add_argument("--output-stem", type=Path, default=None)
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()

    d, m = args.case
    solutions = load_solutions(args.solutions)
    if (d, m) not in solutions:
        raise SystemExit(f"solutions pkl に (D={d}, M={m}) がありません。keys={sorted(solutions)[:6]}...")
    assignment = solutions[(d, m)]

    with args.distance_matrix.open("rb") as f:
        order = pickle.load(f)["order"]
    bridges = pd.read_csv(args.bridges)
    coords = coords_in_assignment_order(bridges, order)
    if len(coords) != assignment.shape[0]:
        raise SystemExit(f"座標数 {len(coords)} と割当行数 {assignment.shape[0]} が不一致。")
    assigned_clusters = np.argmax(assignment, axis=1)

    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    print(f"D={d}, M={m}:")
    ok = verify_case(assignment, args.results_csv, d, m, args.bundle_limit, q)
    if not ok and not args.no_verify:
        raise SystemExit("検証失敗: 割当が結果CSVと一致しません（--no-verify で無視可）。")

    gdf, union = load_admin_boundaries_gdf(args.boundary, municipalities=MUNICIPALITIES)
    cluster_polygons = bridge_based_voronoi(coords, assigned_clusters, union)
    fig, _ = plot_voronoi_map(
        cluster_polygons, coords, assigned_clusters, boundary_gdf=gdf,
        bounds=union.bounds if union is not None else None,
        title=f"$D={int(d)}$ km, $M={m}$",
    )

    stem = args.output_stem or Path(f"figures/districting_map_D{int(d)}_M{m}")
    stem.parent.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in [("png", {"dpi": 300}), ("svg", {}), ("pdf", {})]:
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
