# paper-bundling-analysis

広域連携による橋梁群の維持管理最適化に向けた地域分割と集約効果の定量分析。査読論文の作業リポジトリ。

## 論文の主題

市町村が管理する橋梁群を対象に、広域連携エリアの空間分割を混合整数計画（MIP）で最適化し、契約バンドリングによる期待契約件数削減効果を定量評価する。

## 正本・主要ドキュメント

- **論文本文**: `paper/latex/main.tex`（LuaLaTeX、ASCEスタイル）
- **調達論点整理レポート**: `references/pdf/調達バンドリング_勉強/橋梁補修工事の契約バンドリング_調達論点整理.md`（理論整理・モデル・新規性の主要参照元）
- **国際比較メモ**: `references/pdf/勉強/米国の管理階層と日本との比較.md`

## ディレクトリ構成

```
paper/
  latex/main.tex        # 論文本文（正本）
  drafts/               # 章ごとの草稿（s01_, s02_, ... で番号付き）
    s01_introduction.md
  planning/             # 設計・構成メモ（outline, methodology, issues 等）
  archive/              # 旧版（学会投稿版 .docx 等）
references/
  pdf/調達バンドリング_勉強/  # 理論整理・既往研究レビュー・モデル設計（主要）
  pdf/勉強/                  # 国際比較・制度調査メモ
  qiao2026_review.md         # Qiao et al. (2026) レビュー
notes/                  # 作業メモ・検討記録（pre_git_migration_inventory.md, step3_refactoring.md が特に重要）
data/                   # 派生データ（data/README.md 参照。生データは data/raw/ か data/external/ に置きGit管理外）
src/bundling_analysis/  # 再利用可能なコアロジック（下記「数値計算パイプライン」参照）
scripts/                # CLIとして実行するステップ別スクリプト
notebooks/              # パイプラインを上から実行して確認するノートブック（下記「プログラムを触るときの起点」）
docs/                   # 環境構築・運用ガイド、非接続コードの一覧
tests/                  # pytest（合成データによる通しテスト、q の出所の検証）
```

## プログラムを触るときの起点

**`notebooks/pipeline_walkthrough.ipynb` を上から実行する。** 計算そのものは `scripts/` 配下の
プログラムが行い、ノートブックはそれらを順に呼び出して、入力・出力・途中の値が繋がっているかを
確認する。どのプログラムが何を受け取り何を出すかは、ここを読むのが最も早い。

- 既定では論文が参照するファイルに触れず、`outputs/walkthrough/<実行時刻>/` に出力して突合する。
- 論文の図表を作り直すときも、このノートブックの第6章を通して実行する（図の生成経路はここに一本化した）。
- 動作はスイッチで切り替える。`RUN_FROM_RAW`（点検データから回すか）、`RUN_GUROBI`（最適化を解き直すか）、
  `RUN_MAPS`（地図を描くか）、`UPDATE_CANONICAL`（`figures/`・`outputs/` を更新するか）、
  `SYNC_TEX_FIGURES`（`main.tex` が読む場所へ図を配るか）。
- 各段階の確認結果は ✅ / ❌ で表示され、最後に一覧表と `run.meta.json`（git HEAD・スイッチ・生成物）が残る。

## ドキュメント案内（mdファイルが多くて迷ったらここを見る）

このREADME.mdが**唯一の起点（base）**。

### ★ 現状を知りたければまずこの2つ

- **`notes/pre_git_migration_inventory.md`** — リポジトリ全体のマスター台帳。どのプログラム・データがどこにあり、何を計算し、複数バージョンのうちどれを採用するかの決定が全部書いてある。**迷ったらまずここ。**
- **`notes/step3_refactoring.md`** — STEP3（メイン解析）をノートブックからスクリプト群へ切り出した記録。各スクリプトが元のどのセルに対応するか、実データでの検証結果が書いてある。同章が指摘していた本文との不整合（`tab:transition_counts`のII→II、`tab:optimization_results`の基準値）は、2026-08-13時点でいずれも `main.tex` 側が更新され解消済み。

パイプラインの現在の姿（何がどこから来て、どこへ繋がっているか）は、上記2つよりも
`notebooks/pipeline_walkthrough.ipynb` を実行するのが早い。上の2つは経緯と決定の記録として参照する。

この2つ以外の`notes/`配下は、**そこに至るまでの検討過程・経緯の記録**であり、内容が古くなっている場合がある（矛盾があれば上記2つを正とする）。

| ファイル | 役割（検討過程・経緯） |
|---|---|
| `source_materials_inventory.md` | 初期段階の参照元フォルダ一覧（→内容は`pre_git_migration_inventory.md`に統合済み） |
| `code_migration.md` | 最初期のコード移植メモ |
| `numerical_results_inventory.md` | 秋大会正本docxから読み取った数値・図表の確認記録 |
| `closed_form_expected_contracts.md` | 期待契約件数の閉形式導出の位置付けメモ |
| `figure2_fit_recovery.md` | 秋大会当時の旧フィッティング式の復元記録（現在は不採用、経緯として参照） |
| `20251208_code_findings.md` | `20251208_定期打ち合わせ`のコード調査メモ |
| `midterm_diff_triage.md` | 中間審査資料のうち本文に含めない内容の整理 |
| `procurement_bundling_issues.md` | バンドリング・発注効率化・距離制約の実務的意味の検討メモ |
| `workflow_consultation.md` | 作業方針の決定事項ログ |

### `paper/` 配下（論文執筆そのもの）

- `paper/latex/main.tex` — 本文の正本
- `paper/drafts/` — 章ごとの下書き（`s01_introduction.md`のように章番号で管理）
- `paper/planning/` — 章立て・方法論・目的関数設計・結果方針などの設計メモ（`outline.md`, `methodology.md`, `objective_design.md`, `manuscript_design.md`, `results.md`/`results_plan.md`, `issues.md`, `improvement_roadmap.md`, `source_docx_summary.md`, `claudecode_prompt.md`）
- `paper/archive/` — 学会投稿版など旧版の原本（docx等）

### `docs/` 配下（環境構築・運用ガイド、Windows/Gurobi関連）

| ファイル | 役割 |
|---|---|
| `gurobi_setup_log.md` | Windows PCでのGurobi環境構築・ライセンストラブル対応ログ |
| `remote_gurobi_setup.md` | 別PCでの地域分割最適化の再実行手順 |
| `multi_pc_git_python_notes.md` | Mac/Windows間のgit・Python環境の詰まりどころ集（認証・pushエラー・VS Code Remote切断対策等） |
| `cli_scripts_guide.md` | CLIスクリプトの引数の渡し方と、各スクリプトのオプション一覧 |
| `legacy_and_unused.md` | 現行パイプラインから外れているコード・データの一覧（触らなくてよいものの明示） |

### その他

- `data/README.md`, `outputs/README.md` — 各ディレクトリの中身の説明
- `references/README.md` — 参考文献の置き場の説明（`references/pdf/`配下の個別レビューメモは文献調査の内容そのもの）
- `tests/test_step3_pipeline.py` — STEP3の合成データによる通しテスト（コードのdocstring参照）
- `tests/test_transition_matrix_provenance.py` — q の出所の検証（推定用データ→推定→保存ファイル→定数の一致）
- `notebooks/pipeline_walkthrough.ipynb` — パイプライン全体を実行して確認するノートブック（上記「プログラムを触るときの起点」）

## 数値計算パイプライン

論文の数値計算は3ステップで構成される（詳細は`notes/pre_git_migration_inventory.md` 2-2b章・7章）。

1. **77条調査（x-Road）生データの取得** — 別プロジェクト（`20250813_xroad取得`）で取得済み。本リポジトリでは再実行しない。
2. **道路メンテナンス年報との施設番号突合（マッチング）** — 同じく別プロジェクトの成果物を所与とする。
3. **メイン解析（本リポジトリの中心）** — RC橋抽出 → 6市町村フィルタ（N=322） → eMarkov推定 → 期待契約件数 → 地域分割最適化。

### ステップ3を構成するスクリプト

上流（点検データ→対象橋梁→推定用データ→距離行列）:

| ファイル | 役割 |
|---|---|
| `scripts/step3_extract_rc_bridges.py` | x-Road原データ→宮城県抽出→RC橋抽出→行政界チェック（期待値5,525件） |
| `scripts/step3_filter_target_municipalities.py` | 対象6市町村（七ヶ宿町・白石市・蔵王町・川崎町・村田町・大河原町）フィルタ。N=322の決定ロジック |
| `scripts/step3_prepare_markov_input.py` | 年報突合データ→供用開始時点付加→eMarkov入力整形（4シナリオ） |
| `scripts/step3_run_emarkov.py` | eMarkov推定の実行。推移確率行列と q を出力する（**q の出所**） |
| `scripts/step3_build_distance_matrix.py` | 橋梁間距離行列の構築（大円距離、`distance_cache.py`のSQLiteキャッシュ経由） |

最適化:

| ファイル | 役割 |
|---|---|
| `scripts/run_gurobi_districting.py` | 地域分割最適化本体（距離制約D×地域数Mの感度分析、Gurobi必須） |
| `scripts/reevaluate_optimization_objectives.py` | GurobiのPWL近似結果を厳密な閉形式で再評価（`--input`・`--output` 必須） |
| `scripts/step3_compare_and_report.py` | 現行管理者ベースとの比較レポート（任意。本文の基準値は作図側で計算する） |

図表:

| ファイル | 出力（本文での位置） |
|---|---|
| `scripts/plot_study_area_map.py` | 対象6市町と322橋の分布（Figure 1） |
| `scripts/plot_inspection_interval.py` | 点検間隔の分布（Figure 2） |
| `scripts/plot_expected_contracts_by_limit.py` | \(f(N,L)\) の形状（Figure 3） |
| `scripts/plot_dm_sensitivity.py` | 距離上限と地域数に対する期待契約件数（Figure 4） |
| `scripts/plot_region_breakdown.py` | 代表解の地域別内訳（Figure 5） |
| `scripts/make_districting_maps.py` / `plot_districting_map.py` | 代表3ケースの地域分割図（Figure 6）とatlas |
| `scripts/make_transition_counts.py` | 健全度遷移の集計表（Table 1） |
| `scripts/plot_optimization_results.py` | 現行管理との比較表（Table 2）のLaTeX行。図自体は本文未使用 |
| `scripts/plot_expected_contracts_scaling_analysis.py` | 第4.3節向けの感度分析図（本文へは未挿入） |

非接続・非推奨のもの（`scripts/make_all_figures.py`, `generate_expected_contracts.py`,
`parallel_contracts.py`, `extract_pdf_text.py`）は `docs/legacy_and_unused.md` を参照。

### コアモジュール

| ファイル | 役割 |
|---|---|
| `src/bundling_analysis/emarkov_estimator.py` | 劣化推移確率（マルコフ行列）の推定（MATLAB版`eMarkov.m`の移植、乱数なし＝決定的） |
| `src/bundling_analysis/expected_contracts.py` | 閉形式の期待契約件数関数と q の算出。`DEFAULT_TRANSITION_MATRIX` は `data/processed/emarkov_20251207_200558/` に保存した推定結果を読み込む（論文が依拠した値をピン留めしてあり、ずれれば警告） |
| `src/bundling_analysis/distance_cache.py` | 橋梁間距離（haversine）のSQLiteキャッシュ |
| `src/bundling_analysis/districting_map.py` | 割当pklの読み込みと地域分割図の描画 |
| `src/bundling_analysis/admin_boundary.py` | 行政界データ読込の統一ローダ（geopandas/pyogrio の版差を吸収） |
| `src/bundling_analysis/preprocessing.py` | 和暦変換・緯度経度パース等の純粋関数 |
| `src/bundling_analysis/plotting_utils.py` | 日本語フォント設定など可視化の共通ユーティリティ |
| `src/bundling_analysis/config.py` | 旧設定クラス。現在使われているのは `SHAPEFILE_PATH` のみ（`I`(=L)等は未使用。`docs/legacy_and_unused.md`） |

Gurobiは別PC（ライセンス保有機）での実行を前提とする（`docs/gurobi_setup_log.md`, `docs/remote_gurobi_setup.md`）。地域分割最適化のフルグリッド（36ケース）は全整数PWLで実行済みで、結果は `data/processed/optimization_results_exact_objective.csv`、割当は `districting_solutions_all36.pkl` にある。

## 論文の構成（main.tex現状）

1. はじめに（群マネの背景・本研究の目的）
2. 既往研究（劣化モデル系 / 契約バンドリング系 / District Optimization系）
3. モデル構築（MIP定式化・マルコフ劣化モデル・閉形式期待契約件数関数）
4. 数値計算（宮城県RC橋、マルコフ推移確率推定・最適化結果）
5. 終わりに

## 研究ポジショニング（三研究群との対比）

| 研究群 | 補修需要の内生化 | 契約ロット設計 | 空間分割最適化 | 代表文献 |
|---|---|---|---|---|
| 確率的維持管理系 | ○ | ✗ | △ | Nakazato et al. 2023, Mizutani et al. 2025 |
| 契約バンドリング系 | ✗（外生） | ○ | △ | Qiao 2018/2021, Miralinaghi 2022 |
| District Optimization系 | ✗ | ✗ | ○ | Kalcsics 2019, Bozkaya 2003 |
| **本研究** | **○** | **○** | **○** | 三系統の統合定式化 |

## 本研究の新規性（3点）

1. **問題設定**: 三研究群が断絶して発展してきた領域を一つの最適化問題として統合定式化
2. **方法論**: 点検データ→マルコフ遷移確率→補修需要確率→期待契約件数 という工学データから調達評価への接続パイプライン
3. **実証・政策**: 橋梁数・地域数・距離制約と期待契約件数の関係を実データで体系的に定量化

## 直近の作業状況

### 2026-08-13

- `notebooks/pipeline_walkthrough.ipynb` を追加。点検データから図表までを上から実行して確認できる。
  原データからの再現（`RUN_FROM_RAW`）、最適化の解き直し（`RUN_GUROBI`）、正本の更新
  （`UPDATE_CANONICAL`）、`main.tex` への図の同期（`SYNC_TEX_FIGURES`）を切り替えられる。
- q の出所をリポジトリ内に移した。従来は `expected_contracts.py` に数値を直接書き、根拠ファイルは
  リポジトリ外にしかなかった。推定結果を `data/processed/emarkov_20251207_200558/` に保存し、
  それを読み込む形に変更。ピン留め値とずれれば警告し、pytestでも検証する。
- 第4.3節向けに `plot_expected_contracts_scaling_analysis.py` を追加（本文へは未挿入）。
- `reevaluate_optimization_objectives.py` の既定値が正本を壊す問題を修正（引数を必須化）。
- 旧系列 `optimization_results_closed_form_20251207_200558.csv` を管理対象から外した（git履歴には残る）。
- 図表生成の経路をノートブック第6章に一本化し、`make_all_figures.py` を非推奨にした。
- 行政界ファイルの読み込みが geopandas と fiona の版の組み合わせで落ちる問題を修正。

### 完了
- `米国の管理階層と日本との比較.md` Section 3-6（国際比較 9ヶ国）: 完了
- `米国の管理階層と日本との比較.md` Chapter 4（4-1〜4-6、4類型整理）: 完了
- `paper/drafts/s01_introduction.md`（Section 1 はじめに草稿）: 完了（2026-07-11）

### 完了（2026-07-11、続き）
- main.tex Section 2（既往研究）にGooijer et al. (2024) 引用を追加（Qiao et al. 2026の直後、Type Bの位置付けで1文）。
- main.tex Section 2にType C背景段落を追加（Cerema/仏、ADEPT/英、Austroads/豪、Te Ringa Maimoa/NZ、FMS/韓を1段落で整理、表1の直後）。
- main.tex Section 2にType A/B/C/D 4類型表（`tab:typology`）を追加し、末尾の新規性宣言をType D位置付けに接続する形へ書き換え。
- 新規`\bibitem`を7件追加：`gooijer2024`, `cerema2024`, `adeptnbg`, `austroads2021`, `teringamaimoa`, `koreafms`, `asce2021bridges`。
- 括弧・環境の対応、`\cite`と`\bibitem`の対応は確認済み（サンドボックス環境にluatexja-presetがないため実コンパイルは未実施。ローカル環境でのコンパイル確認が必要）。

### main.tex に未反映（次セッションで対応予定）

**Section 1（はじめに）のmain.tex統合**
- `paper/drafts/s01_introduction.md` は完成（2026-07-11）。ASCE 2021 Infrastructure Report Card (Bridges) を冒頭引用として採用し、サブセクション見出しなしの1本の文章に統合済み。`asce2021bridges`の`\bibitem`はmain.texに追加済みだが、Introduction本文自体のmain.tex統合（既存の「はじめに」セクションの置き換え）は未実施。
- 統合時の要判断：本文で「State DOT District 800〜1,300橋」の出典を`fhwa2019`（FHWA Bridge Bundling Guidebook, 2019）に統一するか、ドラフトが使うFDOT (2021) を別途`\bibitem`として追加するか（ドラフト末尾の残課題参照）。

## 主要パラメータ（数値計算）

- 対象: 宮城県内6市町村（七ヶ宿町・白石市・蔵王町・川崎町・村田町・大河原町）のRC橋 **322橋**（推移確率推定自体は宮城県内RC橋5,525橋のデータを使用）
- 補修確率: q = 0.012329787974114258（`with_supply_collapse`系）。`data/processed/markov_input_20251207_200558/` の推定用データから `step3_run_emarkov.py` で再現でき、その出力を `data/processed/emarkov_20251207_200558/` に保存して `expected_contracts.py` が読み込む。整合は `tests/test_transition_matrix_provenance.py` が検証する
- 同時発注上限: L = 5（基準値）、感度分析L = 1, 3, 7, 10
- 距離制約 D・地域数 M を政策変数として感度分析（本文主結果は全整数PWL、`data/processed/gurobi_validation_all_integer.csv`）

数値の根拠・複数系列の採否判断は `notes/pre_git_migration_inventory.md` を参照。
