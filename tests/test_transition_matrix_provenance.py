# -*- coding: utf-8 -*-
"""q の出所を機械的に縛るテスト。

論文の全数値は q に依存し、q は推移確率行列から決まる。その行列は
コミット済みの eMarkov 入力TSVから決定的に再現できるはずなので、
「TSV → 推定 → ファイル → 定数」の各段がずれていないことをここで断言する。

これが落ちたときの意味:
  * test_committed_output_matches_pin
        eMarkov出力ファイルが、論文が依拠するピン留め値からずれた。
        意図した更新なら OPTIMIZATION_TRANSITION_MATRIX も更新する。
  * test_estimation_reproduces_committed_output
        コミット済みTSVから再推定しても出力ファイルに一致しない。
        推定器のコードが変わったか、ファイルが手で書き換えられた。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from bundling_analysis.expected_contracts import (  # noqa: E402
    CANONICAL_TRANSITION_MATRIX_PATH,
    DEFAULT_TRANSITION_MATRIX,
    OPTIMIZATION_TRANSITION_MATRIX,
    load_transition_matrix,
    repair_probability_from_transition_matrix,
)

MARKOV_INPUT_DIR = REPO_ROOT / "data/processed/markov_input_20251207_200558"
SCENARIO = "with_supply_collapse"

#: 論文本文・図表が依拠している値。ここを書き換えるときは本文も見直すこと。
PAPER_Q = 0.012329787974114258


def test_canonical_output_is_committed() -> None:
    """q の根拠ファイルがリポジトリ内にあること（外部フォルダ依存にしない）。"""
    assert CANONICAL_TRANSITION_MATRIX_PATH.exists(), (
        f"{CANONICAL_TRANSITION_MATRIX_PATH} が無い。"
        " scripts/step3_run_emarkov.py で再生成すること。"
    )


def test_committed_output_matches_pin() -> None:
    """コミット済みeMarkov出力が、ピン留めした行列と完全一致すること。"""
    loaded = load_transition_matrix(CANONICAL_TRANSITION_MATRIX_PATH)
    assert loaded == OPTIMIZATION_TRANSITION_MATRIX
    assert DEFAULT_TRANSITION_MATRIX == loaded


def test_q_matches_paper_value() -> None:
    """導かれる q が論文の値と完全一致すること。"""
    _, q = repair_probability_from_transition_matrix(DEFAULT_TRANSITION_MATRIX)
    assert q == PAPER_Q


@pytest.mark.skipif(
    not (MARKOV_INPUT_DIR / f"markov_input_{SCENARIO}.txt").exists(),
    reason="eMarkov入力TSVが無い",
)
def test_estimation_reproduces_committed_output(tmp_path: Path) -> None:
    """コミット済みTSVから再推定すると、出力ファイルに一致すること。

    ここが ② → ③ の接続の本体。推定器は乱数を使わず決定的なので、
    入力が同じなら出力もビット単位で同じになるはず。
    """
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/step3_run_emarkov.py"),
            "--input-dir", str(MARKOV_INPUT_DIR),
            "--scenarios", SCENARIO,
            "--output-dir", str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    rerun = load_transition_matrix(
        tmp_path / SCENARIO / f"{SCENARIO}_transition_matrix_stage3.csv"
    )
    assert rerun == load_transition_matrix(CANONICAL_TRANSITION_MATRIX_PATH)

    _, q = repair_probability_from_transition_matrix(rerun)
    assert q == PAPER_Q
