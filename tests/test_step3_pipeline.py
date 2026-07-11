# -*- coding: utf-8 -*-
"""STEP3パイプラインの合成データによる通し（end-to-end）テスト。

実データ（x-Road原データ・道路メンテナンス年報）は使わず、スキーマだけを
模した小規模な合成データで、5本のSTEP3スクリプトが連携して動くことを
検証する。Gurobiは使わない（`step3_compare_and_report` は合成の割当行列
で代替する）。

実行:
    pip install -e ".[dev]"
    pytest tests/test_step3_pipeline.py -v
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from step3_extract_rc_bridges import extract_rc_bridges, load_xroad_prefecture  # noqa: E402
from step3_filter_target_municipalities import (  # noqa: E402
    TARGET_ADMINS,
    filter_target_municipalities,
)
from step3_prepare_markov_input import (  # noqa: E402
    add_supply_start_rows,
    build_matched_history,
    clean_history,
    prepare_markov_input,
)
from step3_build_distance_matrix import build_distance_matrix  # noqa: E402
from step3_compare_and_report import admin_baseline, objective_from_assignment  # noqa: E402


# 6市町村のうち4つを対象(target)に、2つを対象外(non-target)として混在させる
TARGET_SAMPLE = TARGET_ADMINS[:4]
NON_TARGET_SAMPLE = ["仙台市", "石巻市"]

# 緯度経度は宮城県内(白石市〜大河原町周辺)に散らす。shisetsu_id は "lat, lon" 文字列。
_COORDS = [
    (38.00, 140.62), (38.02, 140.65), (38.05, 140.60), (38.08, 140.68),
    (38.10, 140.70), (38.12, 140.55), (38.15, 140.58), (38.18, 140.63),
    (38.20, 140.66), (38.22, 140.61),
]
_ADMINS = [
    TARGET_SAMPLE[0], TARGET_SAMPLE[1], TARGET_SAMPLE[2], TARGET_SAMPLE[3],
    NON_TARGET_SAMPLE[0], TARGET_SAMPLE[0], NON_TARGET_SAMPLE[1], TARGET_SAMPLE[1],
    TARGET_SAMPLE[2], TARGET_SAMPLE[3],
]
# 構造区分コード。百の位=3がRC。index 5, 7 は非RC（百の位=1）でRC抽出のテストに使う。
_STRUCTURES = [301, 302, 310, 305, 300, 150, 320, 100, 315, 308]
_KASETSU = ["S55", "H2", "H10", "R1", "H20", "H15", "S60", "H5", "H25", "R3"]

EXPECTED_RC_COUNT = 8  # 10橋中、非RC2橋(index5,7)を除いた数
EXPECTED_TARGET_COUNT = 6  # RC8橋中、対象6市町村に属する数（index4,6が対象外）


def _make_xroad_csv(path: Path) -> None:
    rows = []
    for i in range(10):
        lat, lon = _COORDS[i]
        rows.append(
            {
                "shisetsu_id": f"{lat}, {lon}",
                "tenken.kiroku.hantei_kubun": (i % 3) + 1,
                "syogen.gyousei_kuiki.todoufuken_mei": "宮城県",
                "syogen.gyousei_kuiki.shikuchouson_mei": _ADMINS[i],
                "syogen.shisetsu.meisyou": f"テスト橋{i + 1}",
                "syogen.rosen.meisyou": f"路線{i + 1}",
                "syogen.kanrisya.meisyou": _ADMINS[i],
                "syogen.kouzou_keishiki.joubu": _STRUCTURES[i],
                "syogen.kasetsu_nendo": _KASETSU[i],
                "shisetsu_bangou": f"B{i + 1:03d}",
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


# 施設番号ごとの点検履歴（年度, 判定）。B006, B008相当は非RC橋なので登場しない想定。
_HISTORY_SPEC = {
    "B001": [("H28", "I"), ("R1", "I"), ("R4", "II")],
    "B002": [("H26", "I"), ("H30", "II"), ("R3", "II")],
    "B003": [("R1", "II"), ("R4", "III")],
    "B004": [("H27", "I"), ("R2", "I")],
    "B009": [("H29", "I"), ("R3", "II")],
    "B010": [("R1", "I"), ("R4", "I")],
}


def _make_maintenance_csv(path: Path) -> None:
    rows = [
        {"matched_shisetsu_bangou": facility, "fiscal_year": year, "hantei": hantei}
        for facility, records in _HISTORY_SPEC.items()
        for year, hantei in records
    ]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


@pytest.fixture()
def synthetic_dir(tmp_path: Path) -> Path:
    _make_xroad_csv(tmp_path / "xroad_miyagi_synthetic.csv")
    _make_maintenance_csv(tmp_path / "maintenance_synthetic.csv")
    return tmp_path


def test_step1_extract_rc_bridges(synthetic_dir: Path) -> None:
    df = load_xroad_prefecture(synthetic_dir / "xroad_miyagi_synthetic.csv")
    assert len(df) == 10
    df_rc = extract_rc_bridges(df)
    assert len(df_rc) == EXPECTED_RC_COUNT
    assert set(df_rc["構造上部_百の位"].unique()) == {3}


def test_step2_filter_target_municipalities(synthetic_dir: Path) -> None:
    df = extract_rc_bridges(load_xroad_prefecture(synthetic_dir / "xroad_miyagi_synthetic.csv"))
    # load_xroad_prefecture が RENAME_MAP 経由で既に「管理者」列を生成している（rename不要）
    subset = filter_target_municipalities(df)
    assert len(subset) == EXPECTED_TARGET_COUNT
    assert set(subset["管理者"].unique()).issubset(set(TARGET_ADMINS))


def test_step3_prepare_markov_input(synthetic_dir: Path) -> None:
    df = extract_rc_bridges(load_xroad_prefecture(synthetic_dir / "xroad_miyagi_synthetic.csv"))
    df["施設番号"] = df["shisetsu_bangou"].astype(str)
    df["架設年度"] = df["syogen.kasetsu_nendo"]
    maint_df = pd.read_csv(synthetic_dir / "maintenance_synthetic.csv", dtype=str).fillna("")

    history = clean_history(build_matched_history(df, maint_df))
    assert history["match"].nunique() == len(_HISTORY_SPEC)

    history_with_supply = add_supply_start_rows(history, df)
    assert len(history_with_supply) == len(history) + len(_HISTORY_SPEC)

    markov_input = prepare_markov_input(history_with_supply, "with_supply_collapse", collapse_iv=True)
    assert not markov_input.empty
    assert {"matched_shisetsu_bangou", "before", "after", "interval"}.issubset(markov_input.columns)
    assert (markov_input["interval"] > 0).all()
    assert (markov_input["interval"] <= 30).all()


def test_step4_build_distance_matrix(synthetic_dir: Path, tmp_path: Path) -> None:
    df = extract_rc_bridges(load_xroad_prefecture(synthetic_dir / "xroad_miyagi_synthetic.csv"))
    df["shisetsu_id"] = df["shisetsu_id"].astype(str)
    order, d_core = build_distance_matrix(df, db_path=str(tmp_path / "dist_cache_test.sqlite"))

    n = len(order)
    assert n == EXPECTED_RC_COUNT
    assert d_core.shape == (n, n)
    assert np.allclose(np.diag(d_core), 0.0)
    assert np.allclose(d_core, d_core.T)
    # 宮城県内スケール(概ね数km〜数十km)の非ゼロ距離であること
    off_diag = d_core[~np.eye(n, dtype=bool)]
    assert (off_diag > 0).all()
    assert off_diag.max() < 200.0


def test_step5_compare_and_report(synthetic_dir: Path, tmp_path: Path) -> None:
    df = extract_rc_bridges(load_xroad_prefecture(synthetic_dir / "xroad_miyagi_synthetic.csv"))
    df["shisetsu_id"] = df["shisetsu_id"].astype(str)
    # load_xroad_prefecture が RENAME_MAP 経由で既に「管理者」列を生成している（rename不要）
    order, d_core = build_distance_matrix(df, db_path=str(tmp_path / "dist_cache_test2.sqlite"))
    assert order == list(df["shisetsu_id"])  # build_distance_matrix はdf順を保持する

    q = 0.0123298551614958  # pptx逆算値と同オーダー（notes/pre_git_migration_inventory.md 0-2章）
    n = len(df)

    baseline = admin_baseline(df, d_core, bundle_limit=5, repair_probability=q)
    assert baseline["objective"] > 0
    assert sum(baseline["counts"]) == n

    # 合成の最適化結果: 全橋を1地域にまとめた場合、目的関数値は必ず管理者ベース以下になるはず
    # （地域統合ほど期待契約件数が逓減するという規模の経済の性質）
    assignment_m1 = np.ones((n, 1), dtype=int)
    total_m1, counts_m1 = objective_from_assignment(assignment_m1, bundle_limit=5, repair_probability=q)
    assert counts_m1 == [n]
    assert total_m1 <= baseline["objective"]

    # solutions.pkl の2形式（run_gurobi_districting.py形式／ノートブック新形式）を両方読めることを確認
    solutions_flat = {(999.0, 1): {"assignment": assignment_m1}}
    path_flat = tmp_path / "solutions_flat.pkl"
    with path_flat.open("wb") as f:
        pickle.dump(solutions_flat, f)

    from step3_compare_and_report import load_solutions

    loaded_flat = load_solutions(path_flat)
    assert (999.0, 1) in loaded_flat
    assert np.array_equal(loaded_flat[(999.0, 1)], assignment_m1)

    solutions_by_distance = {"by_distance": {999.0: {1: assignment_m1}}}
    path_nested = tmp_path / "solutions_nested.pkl"
    with path_nested.open("wb") as f:
        pickle.dump(solutions_by_distance, f)
    loaded_nested = load_solutions(path_nested)
    assert (999.0, 1) in loaded_nested
    assert np.array_equal(loaded_nested[(999.0, 1)], assignment_m1)
