"""Expected contract counts under contract bundling.

This module implements the closed-form expected contract count used in the
paper draft. It intentionally depends only on the Python standard library so
the formula can be checked without rebuilding the full analysis environment.

``DEFAULT_TRANSITION_MATRIX`` — the matrix every downstream script derives ``q``
from — is **read from the eMarkov output committed in this repository**, not
from a literal typed into this file. The chain is:

    data/processed/markov_input_20251207_200558/markov_input_with_supply_collapse.txt
        |  scripts/step3_run_emarkov.py  (deterministic: no RNG, no seed)
        v
    data/processed/emarkov_20251207_200558/with_supply_collapse/
        with_supply_collapse_transition_matrix_stage3.csv   <-- read at import
        v
    DEFAULT_TRANSITION_MATRIX -> q = 0.012329787974114258

Loading rather than hard-coding means that re-running the estimation on new
inspection data actually reaches the figures and tables. To keep that from
happening *silently*, the value the paper was written against is still pinned
here as ``OPTIMIZATION_TRANSITION_MATRIX``: if the file on disk stops matching
the pin, importing this module warns. A deliberate update therefore means
re-running the estimation **and** updating the pin, at which point the warning
goes away and ``tests/test_transition_matrix_provenance.py`` passes again.

Importing stays cheap and dependency-free: the estimator is not run here, only
its committed output is read (stdlib ``csv``). If the file is missing, the
pinned value is used and a warning is issued, so the module never fails to
import.
"""

from __future__ import annotations

import csv
import warnings
from math import ceil, comb
from pathlib import Path
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

#: eMarkov output this repository treats as canonical. Regenerate in place with
#: ``python scripts/step3_run_emarkov.py
#:     --input-dir data/processed/markov_input_20251207_200558
#:     --scenarios with_supply_collapse
#:     --output-dir data/processed/emarkov_20251207_200558``
CANONICAL_TRANSITION_MATRIX_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "emarkov_20251207_200558"
    / "with_supply_collapse"
    / "with_supply_collapse_transition_matrix_stage3.csv"
)

#: The value the paper was written against. Kept as a pin so that a change in
#: the file above cannot pass unnoticed; update it together with the file.
#: (with_supply series; matches the midterm-review pptx chart4 q within ~5.4e-6.)
OPTIMIZATION_TRANSITION_MATRIX = (
    (9.132011474084255065e-01, 8.616882547596728392e-02, 6.300271156072234646e-04),
    (0.0, 9.857330912701161019e-01, 1.426690872988389813e-02),
    (0.0, 0.0, 1.0),
)


def load_transition_matrix(path) -> tuple[tuple[float, ...], ...]:
    """Read a transition matrix written by ``scripts/step3_run_emarkov.py``.

    The file is a headerless CSV of the m x m matrix (``numpy.savetxt``
    default format), so the values round-trip exactly through ``float``.
    """

    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = [[float(value) for value in row] for row in csv.reader(handle) if row]
    if not rows or any(len(row) != len(rows) for row in rows):
        raise ValueError(f"{path} is not a square transition matrix")
    for index, row in enumerate(rows):
        if abs(sum(row) - 1.0) > 1e-9:
            raise ValueError(f"{path} row {index} sums to {sum(row)!r}, not 1")
    return tuple(tuple(row) for row in rows)


def _canonical_transition_matrix() -> tuple[tuple[float, ...], ...]:
    """Load the committed eMarkov output, warning if it drifts from the pin."""

    if not CANONICAL_TRANSITION_MATRIX_PATH.exists():
        warnings.warn(
            f"canonical transition matrix not found at "
            f"{CANONICAL_TRANSITION_MATRIX_PATH}; falling back to the pinned "
            f"OPTIMIZATION_TRANSITION_MATRIX. Regenerate it with "
            f"scripts/step3_run_emarkov.py.",
            stacklevel=2,
        )
        return OPTIMIZATION_TRANSITION_MATRIX

    loaded = load_transition_matrix(CANONICAL_TRANSITION_MATRIX_PATH)
    if loaded != OPTIMIZATION_TRANSITION_MATRIX:
        _, loaded_q = repair_probability_from_transition_matrix(loaded)
        _, pinned_q = repair_probability_from_transition_matrix(
            OPTIMIZATION_TRANSITION_MATRIX
        )
        warnings.warn(
            "the committed eMarkov output no longer matches the pinned matrix "
            "the paper was written against: "
            f"q = {loaded_q!r} (file) vs {pinned_q!r} (pin). "
            "Every figure and table will now use the file. If that is intended, "
            "update OPTIMIZATION_TRANSITION_MATRIX in "
            f"{Path(__file__).name} to match; if not, restore "
            f"{CANONICAL_TRANSITION_MATRIX_PATH.name}.",
            stacklevel=2,
        )
    return loaded


#: Matrix used by every downstream script. Read from the committed eMarkov
#: output above, so re-running the estimation propagates to the results.
DEFAULT_TRANSITION_MATRIX = _canonical_transition_matrix()
