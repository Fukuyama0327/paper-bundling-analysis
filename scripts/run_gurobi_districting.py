"""Run districting optimization with the closed-form expected-contract objective.

This script is intended for the separate PC that has a working Gurobi license.
It uses a precomputed distance-matrix pickle and can switch between the legacy
20-node PWL approximation and all-integer PWL nodes.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from bundling_analysis.expected_contracts import (
    DEFAULT_TRANSITION_MATRIX,
    expected_contracts,
    repair_probability_from_transition_matrix,
)


def parse_case(value: str) -> tuple[float, int]:
    try:
        distance_text, m_text = value.split(":", maxsplit=1)
        return float(distance_text), int(m_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("case must be formatted as D:M, e.g. 25:3") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Gurobi districting cases for closed-form objective validation."
    )
    parser.add_argument(
        "--distance-matrix",
        type=Path,
        default=Path("data/processed/distance_matrix_322_20251208.pkl"),
        help="Pickle containing {'order': ..., 'd_core': distance_matrix}.",
    )
    parser.add_argument(
        "--cases",
        type=parse_case,
        nargs="+",
        default=[(25.0, 3), (35.0, 3), (40.0, 1)],
        help="Representative cases formatted as D:M, e.g. --cases 25:3 35:3.",
    )
    parser.add_argument(
        "--pwl",
        choices=["all", "20"],
        default="all",
        help="Use all integer N nodes or the legacy 20-node PWL approximation.",
    )
    parser.add_argument("--bundle-limit", type=int, default=5, help="Bundle limit L.")
    parser.add_argument("--threads", type=int, default=0, help="Gurobi thread count; 0 uses default.")
    parser.add_argument("--time-limit", type=float, default=None, help="Optional time limit per case.")
    parser.add_argument("--mip-gap", type=float, default=None, help="Optional relative MIP gap.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/gurobi_districting_validation.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--solutions-output",
        type=Path,
        default=Path("outputs/gurobi_districting_validation_solutions.pkl"),
        help="Output pickle path for assignment matrices.",
    )
    return parser.parse_args()


def load_distance_matrix(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open("rb") as f:
        data = pickle.load(f)
    order = [str(item) for item in data["order"]]
    matrix = np.asarray(data["d_core"], dtype=float)
    if matrix.shape != (len(order), len(order)):
        raise ValueError("distance matrix shape does not match order length")
    return order, matrix


def build_pwl_nodes(num_bridges: int, mode: str) -> list[int]:
    if mode == "all":
        return list(range(1, num_bridges + 1))
    raw_nodes = np.linspace(1, num_bridges, 20)
    nodes = sorted({int(value) for value in raw_nodes})
    if nodes[0] != 1:
        nodes.insert(0, 1)
    if nodes[-1] != num_bridges:
        nodes.append(num_bridges)
    return nodes


def exact_objective(counts: list[int], bundle_limit: int, repair_probability: float) -> float:
    return sum(expected_contracts(count, bundle_limit, repair_probability) for count in counts)


def optimize_case(
    distance_matrix: np.ndarray,
    distance_threshold: float,
    num_regions: int,
    pwl_nodes: list[int],
    y_values: list[float],
    bundle_limit: int,
    repair_probability: float,
    threads: int,
    time_limit: float | None,
    mip_gap: float | None,
) -> tuple[dict[str, object], np.ndarray]:
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except ImportError as exc:
        raise RuntimeError("gurobipy is not installed or not available in this environment") from exc

    num_bridges = distance_matrix.shape[0]
    model = gp.Model()
    if threads > 0:
        model.setParam("Threads", threads)
    if time_limit is not None:
        model.setParam("TimeLimit", time_limit)
    if mip_gap is not None:
        model.setParam("MIPGap", mip_gap)

    z = model.addVars(num_bridges, num_regions, vtype=GRB.BINARY, name="z")
    region_sizes = model.addVars(num_regions, vtype=GRB.INTEGER, name="N_m")
    region_objectives = model.addVars(num_regions, vtype=GRB.CONTINUOUS, name="f_N_m")

    for bridge_index in range(num_bridges):
        model.addConstr(
            gp.quicksum(z[bridge_index, region] for region in range(num_regions)) == 1
        )

    for region in range(num_regions):
        model.addConstr(
            gp.quicksum(z[bridge_index, region] for bridge_index in range(num_bridges)) >= 1
        )
        model.addConstr(
            region_sizes[region]
            == gp.quicksum(z[bridge_index, region] for bridge_index in range(num_bridges))
        )
        model.addGenConstrPWL(
            region_sizes[region],
            region_objectives[region],
            pwl_nodes,
            y_values,
            name=f"pwl_f_expr_{region}",
        )

    # Enforce the regional diameter constraint by forbidding any pair farther
    # than D from being assigned to the same region.
    for i in range(num_bridges):
        for j in range(i + 1, num_bridges):
            if float(distance_matrix[i, j]) > distance_threshold:
                for region in range(num_regions):
                    model.addConstr(z[i, region] + z[j, region] <= 1)

    total_orders = gp.quicksum(region_objectives[region] for region in range(num_regions))
    model.setObjective(total_orders, GRB.MINIMIZE)

    start = time.time()
    model.optimize()
    elapsed = time.time() - start

    if model.SolCount == 0:
        row = {
            "MaxDistance": distance_threshold,
            "M": num_regions,
            "Status": int(model.Status),
            "ObjectiveValue_PWL": "",
            "ObjectiveValue_Exact": "",
            "Difference_PWL_minus_Exact": "",
            "ElapsedSeconds": f"{elapsed:.3f}",
            "RegionCounts": "",
            "PWLNodes": len(pwl_nodes),
            "BundleLimit": bundle_limit,
        }
        return row, np.zeros((num_bridges, num_regions), dtype=int)

    assignment = np.zeros((num_bridges, num_regions), dtype=int)
    for bridge_index in range(num_bridges):
        for region in range(num_regions):
            if z[bridge_index, region].X > 0.5:
                assignment[bridge_index, region] = 1

    counts = [int(assignment[:, region].sum()) for region in range(num_regions)]
    exact = exact_objective(counts, bundle_limit, repair_probability)
    row = {
        "MaxDistance": distance_threshold,
        "M": num_regions,
        "Status": int(model.Status),
        "ObjectiveValue_PWL": f"{float(model.ObjVal):.12f}",
        "ObjectiveValue_Exact": f"{exact:.12f}",
        "Difference_PWL_minus_Exact": f"{float(model.ObjVal) - exact:.12f}",
        "ElapsedSeconds": f"{elapsed:.3f}",
        "RegionCounts": ";".join(str(count) for count in counts),
        "PWLNodes": len(pwl_nodes),
        "BundleLimit": bundle_limit,
    }
    return row, assignment


def main() -> None:
    args = parse_args()

    # 実行時に渡された引数をそのまま表示する。打ち間違い・渡し忘れがないか
    # ここで目視確認できる（notes/pre_git_migration_inventory.md 7-2章「暗黙依存」対策）。
    print("=== 実行パラメータ ===")
    for key, value in sorted(vars(args).items()):
        print(f"  {key}: {value}")

    order, distance_matrix = load_distance_matrix(args.distance_matrix)
    num_bridges = len(order)
    _, repair_probability = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    print(f"  repair_probability (q): {repair_probability!r}")
    print(f"  num_bridges: {num_bridges}")
    pwl_nodes = build_pwl_nodes(num_bridges, args.pwl)
    y_values = [
        expected_contracts(node, args.bundle_limit, repair_probability)
        for node in pwl_nodes
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.solutions_output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "MaxDistance",
        "M",
        "Status",
        "ObjectiveValue_PWL",
        "ObjectiveValue_Exact",
        "Difference_PWL_minus_Exact",
        "ElapsedSeconds",
        "RegionCounts",
        "PWLNodes",
        "BundleLimit",
    ]

    # ケースごとに逐次書き出す（長時間のグリッド実行中にクラッシュしても
    # 完了済みケースの結果が失われないようにするため）。solutions pklも
    # ケースごとに上書き保存する。
    solutions: dict[tuple[float, int], dict[str, object]] = {}
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.flush()
        for case_index, (distance_threshold, num_regions) in enumerate(args.cases, start=1):
            print(f"[case {case_index}/{len(args.cases)}] D={distance_threshold}, M={num_regions}")
            row, assignment = optimize_case(
                distance_matrix=distance_matrix,
                distance_threshold=distance_threshold,
                num_regions=num_regions,
                pwl_nodes=pwl_nodes,
                y_values=y_values,
                bundle_limit=args.bundle_limit,
                repair_probability=repair_probability,
                threads=args.threads,
                time_limit=args.time_limit,
                mip_gap=args.mip_gap,
            )
            writer.writerow(row)
            f.flush()
            solutions[(distance_threshold, num_regions)] = {
                "assignment": assignment,
                "row": row,
                "order": order,
            }
            with args.solutions_output.open("wb") as sf:
                pickle.dump(solutions, sf)

    # 実行条件をJSONサイドカーとして残す。結果CSV単体を後から見ても、
    # どの引数・どのq値で作られたかを追跡できるようにするため。
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "scripts/run_gurobi_districting.py",
        "arguments": {
            "distance_matrix": str(args.distance_matrix),
            "cases": [[d, m] for d, m in args.cases],
            "pwl": args.pwl,
            "bundle_limit": args.bundle_limit,
            "threads": args.threads,
            "time_limit": args.time_limit,
            "mip_gap": args.mip_gap,
            "output": str(args.output),
            "solutions_output": str(args.solutions_output),
        },
        "repair_probability_q": repair_probability,
        "num_bridges": num_bridges,
        "pwl_node_count": len(pwl_nodes),
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".meta.json")
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.output}")
    print(f"Wrote {args.solutions_output}")
    print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
