"""Expected contract counts under contract bundling.

This module implements the closed-form expected contract count used in the
paper draft. It intentionally depends only on the Python standard library so
the formula can be checked without rebuilding the full analysis environment.
"""

from __future__ import annotations

from math import ceil, comb
from typing import Sequence


def repair_probability_from_transition_matrix(
    transition_matrix: Sequence[Sequence[float]],
) -> tuple[tuple[float, ...], float]:
    """Compute single-bridge repair probability from a 3-state transition matrix.

    The current paper model uses two non-repair states and one repair-trigger
    state. For a matrix partitioned as ``P = [[T, r], [0, 1]]``, this computes
    ``pi = e1'(I - T)^-1 / (e1'(I - T)^-1 1)`` and ``q = pi r``.

    This implementation is specialized to the 3-state case to keep the
    dependency footprint small.
    """

    if len(transition_matrix) != 3 or any(len(row) != 3 for row in transition_matrix):
        raise ValueError("transition_matrix must be a 3x3 matrix")

    p11 = float(transition_matrix[0][0])
    p12 = float(transition_matrix[0][1])
    p13 = float(transition_matrix[0][2])
    p22 = float(transition_matrix[1][1])
    p23 = float(transition_matrix[1][2])

    # Inverse of [[1-p11, -p12], [0, 1-p22]], left-multiplied by e1'.
    a = 1.0 - p11
    d = 1.0 - p22
    if a == 0 or d == 0:
        raise ValueError("non-repair transition block must be transient")

    numerator_1 = 1.0 / a
    numerator_2 = p12 / (a * d)
    denominator = numerator_1 + numerator_2
    pi_1 = numerator_1 / denominator
    pi_2 = numerator_2 / denominator
    q = pi_1 * p13 + pi_2 * p23
    return (pi_1, pi_2), q


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

OPTIMIZATION_TRANSITION_MATRIX = (
    (0.9132082586632038, 0.08616179766540086, 0.00062994367139535),
    (0.0, 0.9857337922074478, 0.01426620779255218),
    (0.0, 0.0, 1.0),
)

DEFAULT_TRANSITION_MATRIX = OPTIMIZATION_TRANSITION_MATRIX
