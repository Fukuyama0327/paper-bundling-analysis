# 地域分割最適化の図表 再現・整備 記録

作成日: 2026-07-15
関連計画: `~/.claude/plans/3-hidden-sprout.md`（承認済み）
対象: PPT「数値計算結果（3）行政界設定の最適化」の図の現行系列（全整数点PWL・36ケース）での再作成。
制約: 本文（`paper/latex/main.tex`・`paper/drafts/**`）は変更しない（別セッションで執筆中）。

## 正本入力（すべて `data/processed/`）

| 用途 | ファイル |
|---|---|
| 全36ケース結果（`ObjectiveValue_Exact`, `RegionCounts` 等） | `optimization_results_exact_objective.csv` |
| 対象322橋（緯度/経度/管理者/shisetsu_id） | `target_rc_bridges_322.csv` |
| 距離行列（`{'order','d_core'}`、割当の行順は `order`） | `distance_matrix_322_20251208.pkl` |
| 6市町境界（地図背景/クリップ用、派生） | `target_municipalities_boundary.geojson` |
| q・閉形式 f(N,L) | `src/bundling_analysis/expected_contracts.py`（`DEFAULT_TRANSITION_MATRIX`, q=0.012329787974114258） |

現行管理の基準値 2.588321070916122 は `target_rc_bridges_322.csv` の管理者別件数
[大河原町103, 白石市98, 蔵王町64, 村田町33, 川崎町14, 七ヶ宿町10] に `f(N,5)` を適用した合計。スクリプトが毎回再計算し一致を確認する。

### 6市町境界geojsonの由来

全国2023shp（`config.SHAPEFILE_PATH`）はOneDriveオンライン専用で~250MBのため、宮城のみ2018版shp（`20251208_.../data/N03-180101_04_GML/N03-18_04_180101.shp`）から6市町（`N03_004`）だけを dissolve 抽出して `data/processed/target_municipalities_boundary.geojson`（896KB, git追跡）を作成。地図背景用途につき2018/2023差は無視できる。N=322 を決める抽出パイプライン側は従来どおり2023shpを使用（本メモの地図とは別工程）。

## 生成物（`figures/`, スクリプトは `scripts/`）

割当pkl **不要**（正本CSV/橋梁CSVのみ、Mac完結・検証済み）:

| 図/表 | スクリプト | 出力 | 検証 |
|---|---|---|---|
| D×M感度分析図（各Mの系列、PPT左図） | `plot_dm_sensitivity.py` | `figures/dm_sensitivity.*` | 描画値==CSV `ObjectiveValue_Exact`、基準線2.588321 |
| Study area map（6市町＋322橋、4章冒頭） | `plot_study_area_map.py` | `figures/study_area.*` | 橋梁数322・市町別合計322 |
| 地域規模×期待契約件数 内訳（cell39相当） | `plot_region_breakdown.py` | `figures/region_breakdown.*`, `outputs/region_breakdown.csv` | 各ケース Σf(N_m)==`ObjectiveValue_Exact` |

割当pkl **必要**（地図、Voronoi＋点）:

| 図 | スクリプト | 出力 |
|---|---|---|
| 代表地域分割図（本文、D=25:3 / D=40:1 / D=35:3） | `plot_districting_map.py`（単一）／`make_districting_maps.py`（駆動） | `figures/districting_map_D{D}_M{M}.*` |
| 全D,M atlas（付録・補足） | `make_districting_maps.py` | `figures/atlas/districting_atlas.*` ＋ `atlas.meta.json` |

- 描画中核 `src/bundling_analysis/districting_map.py` は旧 `20251122_.../図表作成/visualize_voronoi_from_saved_results.py` の2関数
  （`bridge_based_voronoi_with_clustering`→`bridge_based_voronoi`, `plot_voronoi_map`）を移植。境界配線は
  旧 `20251206.ipynb` cell 37（`config.SHAPEFILE_PATH` を `N03_001/N03_004` で6市町に絞る）を踏襲。
- 割当行列の行↔橋梁は距離行列 `order`↔`shisetsu_id` で整列（`coords_in_assignment_order`）。
- 各ケースで割当から地域別件数（ソート済み）と厳密目的値を再計算し、CSVの `RegionCounts`・`ObjectiveValue_Exact` と一致を必須検証。
- レンダラは合成割当（k-means）で end-to-end 検証済み（Voronoiクリップ・色・凡例・atlasグリッド）。

## 割当pkl（solutions）の状況 — **未取得（要Windows）**

地図の割当データが現行正本と一致するものはリポジトリに無い。
- 旧 `20251208_.../results/main/20251207_200558/optimization/z_assignments.pkl` は**粗いPWLの別解**で正本と不一致（例 D=15,M=6: 旧2.0539/別分割 vs 正本2.0871）。使用不可。
- 現行の全整数PWL 36ケース（`a3a2f61`）の solutions は Windows 側 `outputs/runs/`（gitignore・未同期）にあるはず。

**次アクション（Windowsで実施）**: 以下いずれかで `data/processed/districting_solutions_all36.pkl` を用意し、`make_districting_maps.py --solutions ...` を実行（Mac可）:
1. **回収**: `a3a2f61` のフルグリッド実行アーカイブ（`outputs/runs/<ts>/` の `--solutions-output` pkl）をコピー。
2. **再実行**: 正本と同コマンドに `--solutions-output` を付す:
   ```
   python scripts/run_gurobi_districting.py --pwl all --cases <全36 D:M> \
       --warm-start-min-m 4 --mip-gap 0.005 \
       --solutions-output data/processed/districting_solutions_all36.pkl --output <tmp.csv>
   ```
   （`docs/multi_pc_git_python_notes.md` 7章のタスクスケジューラ運用）
どちらでも `make_districting_maps.py` の必須検証（36ケースで件数＋Exactが正本CSVと一致）を通ることをゲートとする。

## コミット

- `29162a7` A（感度）・A2（study area）・D（内訳）＋境界ローダ＋境界geojson
- `2429389` 地図レンダラ（`districting_map.py`＋2スクリプト、solutions pkl待ち）
- `df01dbe` 閉形式vsシミュ比較図の retire

push はユーザーの実マシンから。本文ファイルは本タスクで未変更。
