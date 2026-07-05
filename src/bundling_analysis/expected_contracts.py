"""Expected contract counts under contract bundling.

This module implements the closed-form expected contract count used in the
paper draft. It intentionally depends only on the Python standard library so
the formula can be checked without rebuilding the full analysis environment.
"""

from __future__ import annotations

from math import ceil, comb
from typing import Sequence


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve ``matrix @ x = rhs`` by Gaussian elimination with partial pivoting."""

    size = len(matrix)
    augmented = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot_row = max(range(col, size), key=lambda r: abs(augmented[r][col]))
        if abs(augmented[pivot_row][col]) == 0.0:
            raise ValueError("non-repair transition block must be transient")
        augmented[col], augmented[pivot_row] = augmented[pivot_row], augmented[col]
        pivot = augmented[col][col]
        for r in range(size):
            if r == col:
                continue
            factor = augmented[r][col] / pivot
            for c in range(col, size + 1):
                augmented[r][c] -= factor * augmented[col][c]
    return [augmented[i][size] / augmented[i][i] for i in range(size)]


def repair_probability_from_transition_matrix(
    transition_matrix: Sequence[Sequence[float]],
) -> tuple[tuple[float, ...], float]:
    """Compute single-bridge repair probability from an m-state transition matrix.

    The paper model uses ``m - 1`` non-repair states and one repair-trigger
    state (the last state). For a matrix partitioned as ``P = [[T, r], [0, 1]]``,
    this computes ``pi = e1'(I - T)^-1 / (e1'(I - T)^-1 1)`` and ``q = pi r``.

    This is the same general algorithm as ``compute_repair_probability`` in the
    original analysis notebook (``20251208_定期打ち合わせ/20251206.ipynb`` cell 26),
    which drove the actual results; it replaces an earlier 3-state-only closed
    form. Implemented with the standard library only (Gaussian elimination on
    ``(I - T)' x = e1``) so the module stays dependency-free.
    """

    size = len(transition_matrix)
    if size < 2 or any(len(row) != size for row in transition_matrix):
        raise ValueError("transition_matrix must be a square matrix of size >= 2")

    m = size - 1  # number of non-repair (transient) states
    t_block = [[float(transition_matrix[i][j]) for j in range(m)] for i in range(m)]
    r_column = [float(transition_matrix[i][m]) for i in range(m)]

    # e1'(I - T)^-1 equals the solution x of (I - T)' x = e1.
    i_minus_t_transposed = [
        [(1.0 if i == j else 0.0) - t_block[j][i] for j in range(m)] for i in range(m)
    ]
    e1 = [1.0] + [0.0] * (m - 1)
    numerator = _solve_linear_system(i_minus_t_transposed, e1)
    denominator = sum(numerator)
    pi = tuple(value / denominator for value in numerator)
    q = sum(pi_i * r_i for pi_i, r_i in zip(pi, r_column))
    return pi, q


def expected_contracts(num_bridges: int, bundle_limit: int, repair_probability: float) -> float:
    """Return E[ceil(X / L)] for X ~ Binomial(N, q).

    Parameters
    ----------
    num_bridges:
        Number of bridges in the district, ``N``.
    bundle_limit:
        Maximum number of bridges bundled into one contract, ``L``.
    repair_probability:
        Single-bridge repair probability, ``q``.
    """

    if num_bridges < 0:
        raise ValueError("num_bridges must be non-negative")
    if bundle_limit <= 0:
        raise ValueError("bundle_limit must be positive")
    if not 0.0 <= repair_probability <= 1.0:
        raise ValueError("repair_probability must be in [0, 1]")

    expected = 0.0
    for n in range(num_bridges + 1):
        probability = (
            comb(num_bridges, n)
            * (repair_probability**n)
            * ((1.0 - repair_probability) ** (num_bridges - n))
        )
        contracts = ceil(n / bundle_limit) if n > 0 else 0
        expected += probability * contracts
    return expected


COMPARISON_TRANSITION_MATRIX = (
    (0.913206062, 0.0861644998, 0.000629438206),
    (0.0, 0.985745578, 0.0142544221),
    (0.0, 0.0, 1.0),
)

# Full-precision values from
# 20251208_定期打ち合わせ/results/main/20251207_200558/emarkov_results/
#   with_supply_collapse/with_supply_collapse_transition_matrix.csv
# (with_supply series; matches the midterm-review pptx chart4 q within ~5.4e-6).
OPTIMIZATION_TRANSITION_MATRIX = (
    (9.132011474084255065e-01, 8.616882547596728392e-02, 6.300271156072234646e-04),
    (0.0, 9.857330912701161019e-01, 1.426690872988389813e-02),
    (0.0, 0.0, 1.0),
)

DEFAULT_TRANSITION_MATRIX = OPTIMIZATION_TRANSITION_MATRIX
