"""Create a dependency-free SVG plot for the expected-contract comparison."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot simulation vs closed-form expected contracts as SVG."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/expected_contracts_comparison_l5.csv"),
        help="Comparison CSV with N, simulation, and analytic columns.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/expected_contracts_comparison_l5.svg"),
        help="Output SVG path.",
    )
    return parser.parse_args()


def load_series(path: Path) -> tuple[list[float], list[float], list[float]]:
    xs: list[float] = []
    simulation: list[float] = []
    formula: list[float] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            xs.append(float(row["N"]))
            simulation.append(float(row["シミュレーション"]))
            formula.append(float(row["解析解"]))

    return xs, simulation, formula


def polyline(points: list[tuple[float, float]], stroke: str) -> str:
    point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polyline points="{point_text}" fill="none" '
        f'stroke="{stroke}" stroke-width="2.2" />'
    )


def main() -> None:
    args = parse_args()
    xs, simulation, formula = load_series(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    width = 760
    height = 480
    margin_left = 76
    margin_right = 28
    margin_top = 32
    margin_bottom = 64
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    min_x = min(xs)
    max_x = max(xs)
    min_y = 0.0
    max_y = max(max(simulation), max(formula)) * 1.08

    def map_x(value: float) -> float:
        return margin_left + (value - min_x) / (max_x - min_x) * plot_width

    def map_y(value: float) -> float:
        return margin_top + (max_y - value) / (max_y - min_y) * plot_height

    sim_points = [(map_x(x), map_y(y)) for x, y in zip(xs, simulation)]
    formula_points = [(map_x(x), map_y(y)) for x, y in zip(xs, formula)]

    y_ticks = [0.0, 0.3, 0.6, 0.9, 1.2]
    x_ticks = [1, 50, 100, 150, 200, 250, 323]
    x_axis_y = map_y(0.0)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
        '<style>text{font-family:Arial, sans-serif;font-size:13px;fill:#222}</style>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" '
        f'y2="{x_axis_y:.2f}" stroke="#222" />',
        f'<line x1="{margin_left}" y1="{x_axis_y:.2f}" '
        f'x2="{width - margin_right}" y2="{x_axis_y:.2f}" stroke="#222" />',
    ]

    for tick in y_ticks:
        y = map_y(tick)
        parts.append(
            f'<line x1="{margin_left - 5}" y1="{y:.2f}" '
            f'x2="{width - margin_right}" y2="{y:.2f}" stroke="#ddd" />'
        )
        parts.append(
            f'<text x="{margin_left - 12}" y="{y + 4:.2f}" text-anchor="end">'
            f"{tick:.1f}</text>"
        )

    for tick in x_ticks:
        x = map_x(float(tick))
        parts.append(
            f'<line x1="{x:.2f}" y1="{x_axis_y:.2f}" '
            f'x2="{x:.2f}" y2="{x_axis_y + 5:.2f}" stroke="#222" />'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{x_axis_y + 24:.2f}" text-anchor="middle">'
            f"{tick}</text>"
        )

    parts.extend(
        [
            polyline(sim_points, "#3b6fb6"),
            polyline(formula_points, "#d15b2f"),
            '<circle cx="560" cy="58" r="5" fill="#3b6fb6" />',
            '<text x="574" y="63">Simulation</text>',
            '<circle cx="560" cy="82" r="5" fill="#d15b2f" />',
            '<text x="574" y="87">Closed form</text>',
            f'<text x="{width / 2:.2f}" y="{height - 18}" text-anchor="middle">'
            "Number of bridges N</text>",
            '<text transform="translate(22 250) rotate(-90)" text-anchor="middle">'
            "Expected contracts</text>",
            "</svg>",
        ]
    )

    args.output.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
