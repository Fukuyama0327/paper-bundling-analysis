# STEP3リファクタリング実施記録

作成日: 2026-07-06
前提資料: `notes/pre_git_migration_inventory.md`（特に7章）

`20251208_定期打ち合わせ/20251206.ipynb`（全42セル）のSTEP3ロジックを、7-3章の推奨方針に沿ってリポジトリのスクリプト群へ切り出した。いずれもグローバル変数依存を排し、明示的な引数・戻り値を持つ関数＋CLIとして実装した。

## 1. 新規・変更ファイルとセル対応

| ファイル | 対応セル | 内容 |
|---|---|---|
| `src/bundling_analysis/preprocessing.py`（新規） | cell 2, 4, 15, 17 | 和暦変換・緯度経度パース・判定正規化等の純粋関数を集約 |
| `src/bundling_analysis/plotting_utils.py`（新規） | cell 6, 10, 34, 41 | 日本語フォント設定の共通化（7-2章-3の重複解消） |
| `src/bundling_analysis/admin_boundary.py`（新規） | cell 9, 11, 35, 37 | 行政界読込の統一ローダ（7-2章-1の3系統重複解消）。正本は2023年版全国shp（`config.SHAPEFILE_PATH`） |
| `scripts/step3_extract_rc_bridges.py`（新規） | cell 4, 8, 9 | x-Road原データ→宮城県抽出→RC橋抽出→行政界チェック。期待値5,525件 |
| `scripts/step3_filter_target_municipalities.py`（新規） | cell 25 | 6市町村フィルタ（N=322決定ロジック）。期待値と不一致なら警告 |
| `scripts/step3_prepare_markov_input.py`（新規） | cell 13, 15, 17 | 年報突合→times=0付加→eMarkov入力整形（4シナリオ分をTSV出力） |
| `scripts/step3_run_emarkov.py`（新規、2026-07-06追加） | cell 19, 22 | eMarkov推定の実行ラッパー。TSV→推移確率行列（全段階＋Stage3吸収3×3）→q。推定設定はcell 19と同一（MATLAB互換）。当初の切り出しで漏れていた工程で、監査時に発見し追加 |
| `scripts/step3_build_distance_matrix.py`（新規） | cell 30 | 距離行列構築。SQLiteキャッシュに一本化し独自pklキャッシュ層を廃止（7-2章-5）。出力は`{'order','d_core'}`形式で`run_gurobi_districting.py`互換 |
| `scripts/step3_compare_and_report.py`（新規） | cell 39, 40 | 管理者ベース比較＋厳密閉形式による目的関数再評価。z_assignmentsのレガシー形式分岐（7-2章-7）は廃止（対応形式は2つに限定） |
| `src/bundling_analysis/expected_contracts.py`（変更） | cell 26 | 下記2章 |

ノートブックのうち可視化専用セル（cell 5, 11のchoropleth, 34, 38, 41の図生成）は本執筆で当該図を再生成する必要が生じた時点で個別に移植する（既存方針6章の通り）。cell 22-23（シナリオ実行・遷移集計）の`run`フラグ方式（7-2章-6）は、`step3_prepare_markov_input.py`が4シナリオ全てを常に出力する設計に置き換えたため解消。

## 2. `compute_repair_probability` の統一（7-2章-2の解消）

- `repair_probability_from_transition_matrix` を、cell 26と同一の一般m×mアルゴリズム（`pi = e1'(I-T)^{-1}` を正規化し `q = pi·r`）に書き換えた。実装は標準ライブラリのみ（ガウス消去法）で、モジュールの依存フリー性は維持。
- 検証: DEFAULT行列・COMPARISON行列・任意の4×4行列で、cell 26のnumpy実装と `q`・`pi` が誤差1e-15未満で一致することを確認した（2026-07-06）。
- 同時に `OPTIMIZATION_TRANSITION_MATRIX` を `20251207_200558` 実行の `with_supply_collapse_transition_matrix.csv` フル精度値に更新。結果: `q = 0.012329787974114258`（pptx逆算qとの相対差 5.4×10⁻⁶、0-2章の予測通り）。f(322, L) は L=1,3,5,7,10 でpptx値と相対差~1e-5以内。

## 3. cell 32 と `run_gurobi_districting.py` の突き合わせ（7-1章「未検証」の解消）

両者の定式化を比較した結論: **数学的に等価（同じ実行可能領域・同じ目的関数）だが、PWL近似の節点とqの系列に差がある。**

共通点:
- 変数 z（橋梁×地域, binary）、N_m（整数）、f_N_m（連続）
- 制約: 各橋梁は1地域に割当 / 各地域は1橋梁以上 / N_m = Σz / PWLによる f(N_m) 近似
- 距離制約: D超過ペアの同一地域割当禁止（z_i + z_j ≤ 1）
- 目的関数: Σ f_N_m の最小化

相違点と評価:

1. **w変数（ノートブックのみ）**: cell 32はD以内のペアにもbinary変数wと連結制約（w≤z_i, w≤z_j, w≥z_i+z_j-1, dist·w≤D）を張るが、wは目的関数にも他制約にも現れず、`dist·w≤D` は feasibleペアでは常に充足される。つまり**wは実行可能領域に影響しない冗長な変数**で、リポジトリ版（infeasibleペア制約のみ）は等価かつ大幅に軽量。リポジトリ版を正本としてよい。
2. **PWL節点**: cell 32は `np.linspace(1, N, 20)` のfloat 20点。リポジトリ版のデフォルトは全整数節点（`--pwl all`）、`--pwl 20` はlinspaceを整数に丸めて重複排除した近似互換モード（float節点の完全再現ではない）。20点PWLと全整数PWLでD=35,M=3の解が異なることは検証済み（`data/README.md`）で、**本文主結果は全整数PWL（`gurobi_validation_all_integer.csv`）を採用**する方針に変更なし。
3. **qの系列**: cell 32は実行時にアクティブなシナリオの推定行列Pからqを計算する（ノートブック保存状態ではcell 2の`run: True`は`with_supply`）。リポジトリ版は`DEFAULT_TRANSITION_MATRIX`（=`20251207_200558`の`with_supply_collapse`、フル精度）を使用。pptx・本文の数値は後者の系列と一致することが確認済み（0-2章）。
4. **実行範囲**: cell 32はconfigのD×Mグリッド全体を回す感度分析、リポジトリ版は代表ケース指定（`--cases D:M`）。全グリッド再実行が必要になれば`--cases`に列挙すれば足りる。

以上より、`scripts/run_gurobi_districting.py` を地域分割最適化の正本コードとして確定する。

## 3b. 出力ポリシー（タイムスタンプフォルダの廃止と中間生成物の対応表、2026-07-06追記）

ノートブックは実行のたびに `results/main/<タイムスタンプ>/` を作り、その下にHTML地図・図・行列CSV・pkl等を蓄積していた。新スクリプト群では方針を変え、**出力先はCLI引数で明示指定し、タイムスタンプフォルダは自動生成しない**。理由: (1) git管理では「実行履歴の蓄積」ではなく「名前の付いた再現可能な成果物」を置きたい、(2) どの実行がどの結果を生んだかは`.meta.json`サイドカー（`run_gurobi_districting.py`・`step3_run_emarkov.py`で導入済み）で担保する。実行履歴を残したい場合は`--output-dir outputs/emarkov_results/$(date +%Y%m%d_%H%M%S)`のように呼び出し側で指定すればよい。

旧output_dir配下の生成物と新スクリプトの対応:

| ノートブックの旧生成物 | 新スクリプトでの扱い |
|---|---|
| `simulation/markov_input_*.txt`（cell 17） | `step3_prepare_markov_input.py` が同形式で出力。**維持** |
| `emarkov_results/<scenario>/*`（行列・ハザード・β・t値CSV、metrics.json。cell 19） | `step3_run_emarkov.py` が `save_emarkov_result` で同一式を出力＋Stage3吸収3×3とqのJSONを追加。**維持・拡張** |
| `optimization/gurobi_objective_results.csv`, `z_assignments.pkl`（cell 32） | `run_gurobi_districting.py` の結果CSV＋solutions pkl＋meta.json。**維持・拡張**（z_assignmentsの形式は変更、`step3_compare_and_report.py`が両形式対応） |
| 距離行列の`cache/dist_matrices/*.pkl`（cell 30、暗黙キャッシュ） | `step3_build_distance_matrix.py` の明示的な出力pklに変更。**暗黙キャッシュは廃止** |
| `reports/detailed_comparison_simple.csv`（cell 41） | `step3_compare_and_report.py` の比較CSV。**維持（数値部分）** |
| `miyagi_rc_map.html`（OSM地図、cell 8）、choropleth（cell 11）、管理者別棒グラフ（cell 6/10） | **未移植（意図的）**。探索的可視化であり論文図でない。必要になれば移植 |
| 点検間隔ヒストグラム（cell 23）→ `fig:inspection_interval` | ~~未移植~~ → **対応済み（2026-07-11）**: `scripts/plot_inspection_interval.py` |
| フィッティング曲線 図（cell 26）→ `fig:expected_contracts` | 既存の `plot_expected_contracts_svg.py`＋`data/processed/expected_contracts_comparison_l5.csv` でカバー。`figures/`への出力を確認済み。**維持** |
| D vs 目的関数値 図（cell 34）→ `fig:optimization_results` | ~~未移植~~ → **対応済み（2026-07-11）**: `scripts/plot_optimization_results.py`（tab:optimization_resultsのLaTeX行も同時出力） |
| Voronoi図（cell 35-38）、比較レポート図・txt（cell 41） | **未移植（意図的）**。必要時に移植（4章方針の通り） |
| 遷移集計クロス表（cell 23）→ `tab:transition_counts` | ~~未移植~~ → **対応済み（2026-07-11）**: `scripts/make_transition_counts.py` |

## 3c. 論文図表の再現検証と発見事項（2026-07-11）

全図表・計算表を `figures/`・`outputs/` に再現できるようにした。図表→スクリプト→入力データの対応:

| 論文ラベル | スクリプト | 入力（正本） | 検証結果 |
|---|---|---|---|
| `tab:transition_counts` | `make_transition_counts.py` | `data/processed/markov_input_20251207_200558/markov_input_with_supply.txt` | **不整合発見**（下記①） |
| `fig:inspection_interval` | `plot_inspection_interval.py` | 同上（mean=6.46, median=5.0） | 再現OK |
| `fig:expected_contracts` | `plot_expected_contracts_svg.py` | `expected_contracts_comparison_l5.csv` | 再現OK。本文記載の誤差値（MAE 0.005193, 平均相対誤差0.746135%, RMSE 0.005384）は`expected_contracts_comparison_summary.csv`のl=5行と完全一致 |
| `fig:optimization_results` | `plot_optimization_results.py` | `data/processed/optimization_results_exact_objective.csv` | 再現OK。本文の最適化行6つ全てD別最小Exact値と一致 |
| `tab:optimization_results` | `plot_optimization_results.py`（LaTeX行出力） | 同上＋`target_rc_bridges_322.csv` | **不整合発見**（下記②） |

また、x-Road原データ（`prefecture_04_宮城県_12425records_original.csv`）からの実データ通し実行で、RC橋5,525件・N=322・判定内訳（I=104, II=209, III=8, IV=0, その他=1）・管理者別橋梁数を新スクリプトで完全再現した（ステップ3前半の実データ検証完了）。**N=322 vs 323の差の正体も特定**: 「無名橋2号」（白石市管理）1件の座標が福島県側（37.565, 140.361）にあり、行政界チェック（cell 9相当）で除外される。

### 発見した本文の不整合（本執筆時に要修正）

1. **`tab:transition_counts`（II→II）**: 現行docx/main.texの4703（計7,638件）は`20251207_120512`以前の旧データ状態由来。その後の重複履歴除去（同一橋梁の重複点検レコード10件、全てII→II）を経た正本データ（採用推移行列と同一実行`20251207_200558`）では**4693（計7,628件）**。採用行列と整合させるには本文を4693に更新すべき。
2. **`tab:optimization_results`（既存の管理 2.5241）**: この基準値は秋大会旧系列のフィッティング式 f(N)=1.594364941N/(128.7141831+N) を管理者別橋梁数[103,98,64,33,14,10]に適用した値（Σ=2.5241で完全一致を確認）。同表の最適化行は新閉形式系列のため**系列が混在している**。閉形式・フル精度qで統一した基準値は**2.588321**で、低減率は17.3→19.3%（D=15）、52.7→53.9%（D≥40）等に変わる。`plot_optimization_results.py`が統一系列のLaTeX行を出力する。

なお、進行中のフルグリッド再構築（Windows側）完了後は、`reevaluate_optimization_objectives.py`で厳密値を再評価し、その出力を`plot_optimization_results.py --input`に渡せば図表とも最新化される。

### 一括生成と実行履歴（2026-07-11追記）

`scripts/make_all_figures.py` で全図表を一括生成できる。出力は2層構造:

- `outputs/runs/<タイムスタンプ>/` — 実行ごとのアーカイブ（figures/・tables/・各ステップのログ・`run.meta.json`にgit HEADと引数を記録）。上書きされない。`outputs/**`は`.gitignore`対象なのでgitには入らないローカル履歴。
- `figures/`・`outputs/*.csv` — 正本。main.texが参照する固定パスで、git管理なので上書きしてもコミット履歴から復元可能。`--no-canonical`で正本更新を抑制し、試行だけアーカイブに残すこともできる。

あわせて、`fig:optimization_results`の入力CSVが`outputs/`（git管理外）にあった問題を修正し、`data/processed/optimization_results_exact_objective.csv`へ移動した（クローン直後でも図表再現が完結するように）。

## 4. 残タスク

- 図表再生成が必要になった際の可視化セル（choropleth・Voronoi・レポート図）の移植（4章・7-1章参照）。
- **論文図表の再生成スクリプト**（3b章の「要対応」分）: `fig:inspection_interval`（点検間隔ヒストグラム、cell 23）、`fig:optimization_results`（D vs 目的関数値、cell 34）、`tab:transition_counts`（遷移集計クロス表、cell 23）。いずれも入力（markov_input TSV / 最適化結果CSV）は新パイプラインで揃うため、描画部分のみの移植。
- `config.py` の旧プロジェクト由来パラメータ（ALPHA系、Weibull系、`BRIDGE_DATA_FILE`等）の整理。現行パイプラインで実際に使うのは `I`（=L）, `SHAPEFILE_PATH`, `M_RANGE`, `GUROBI_THREADS`, `USE_PWL` 程度。
- ~~実データでの通し実行~~ → **一部完了（2026-07-06）**。Windows PC（`bridge-extract-gpu`環境、Python 3.11.15、Gurobi 10.0.0）で、実際の距離行列（`data/processed/distance_matrix_322_20251208.pkl`）を使い、代表3ケース（D=25:3, 35:3, 40:1）を全整数PWL・20点PWL両方で実行し、`data/processed/gurobi_validation_all_integer.csv` / `gurobi_validation_20_nodes.csv`を更新済み。
  - **重要な確認**: D=35km,M=3で20点PWLと全整数PWLが異なる分割に到達し、20点PWLの厳密再評価値（1.262631045736）は全整数PWLの値（1.262041465559）より悪い（大きい）。**全整数PWLを主結果として採用する既存方針が、実データでも裏付けられた。**
  - ただしステップ1・2（RC橋抽出〜eMarkov入力整形〜推移確率推定）自体の実データ通し実行はまだ行っていない（本項は`distance_matrix_322_20251208.pkl`が既に存在するため、その手前の工程をスキップしてGurobi最適化のみ実データで検証したもの）。
- **進行中**: 全整数PWLでの**フルグリッド**（D=15〜50km、M=2〜6の36ケース、`data/processed/optimization_results_closed_form_20251207_200558.csv`が持つのと同じ組み合わせ）の再構築をWindows側で実行中。完了後、同ファイルを更新し、qのフル精度化（0-2章）を反映した最終版とする。
