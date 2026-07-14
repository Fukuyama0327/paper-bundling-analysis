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
docs/                   # Gurobi実行環境（別PC）のセットアップ記録
```

## ドキュメント案内（mdファイルが多くて迷ったらここを見る）

このREADME.mdが**唯一の起点（base）**。

### ★ 現状を知りたければまずこの2つ

- **`notes/pre_git_migration_inventory.md`** — リポジトリ全体のマスター台帳。どのプログラム・データがどこにあり、何を計算し、複数バージョンのうちどれを採用するかの決定が全部書いてある。**迷ったらまずここ。**
- **`notes/step3_refactoring.md`** — STEP3（メイン解析）をノートブックからスクリプト群へ切り出した記録。各スクリプトが元のどのセルに対応するか、実データでの検証結果、本文との不整合の発見（`tab:transition_counts`のII→II、`tab:optimization_results`の基準値、詳細は3c章）が書いてある。

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
| `cli_scripts_guide.md` | Jupyter Notebookから来た人向け、CLIスクリプト（`--cases`等）の使い方ガイド |

### その他

- `data/README.md`, `outputs/README.md` — 各ディレクトリの中身の説明
- `references/README.md` — 参考文献の置き場の説明（`references/pdf/`配下の個別レビューメモは文献調査の内容そのもの）
- `tests/test_step3_pipeline.py` — STEP3の合成データによる通しテスト（コードのdocstring参照）

## 数値計算パイプライン

論文の数値計算は3ステップで構成される（詳細は`notes/pre_git_migration_inventory.md` 2-2b章・7章）。

1. **77条調査（x-Road）生データの取得** — 別プロジェクト（`20250813_xroad取得`）で取得済み。本リポジトリでは再実行しない。
2. **道路メンテナンス年報との施設番号突合（マッチング）** — 同じく別プロジェクトの成果物を所与とする。
3. **メイン解析（本リポジトリの中心）** — RC橋抽出 → 6市町村フィルタ（N=322） → eMarkov推定 → 期待契約件数 → 地域分割最適化。

### ステップ3を構成するスクリプト・モジュール

| ファイル | 役割 |
|---|---|
| `scripts/step3_extract_rc_bridges.py` | x-Road原データ→宮城県抽出→RC橋抽出→行政界チェック（期待値5,525件） |
| `scripts/step3_filter_target_municipalities.py` | 対象6市町村（七ヶ宿町・白石市・蔵王町・川崎町・村田町・大河原町）フィルタ。N=322の決定ロジック |
| `scripts/step3_prepare_markov_input.py` | 年報突合データ→供用開始時点付加→eMarkov入力整形 |
| `scripts/step3_build_distance_matrix.py` | 橋梁間距離行列の構築（`distance_cache.py`のSQLiteキャッシュに統一） |
| `scripts/run_gurobi_districting.py` | 地域分割最適化本体（距離制約D×地域数Mの感度分析、Gurobi必須） |
| `scripts/step3_compare_and_report.py` | 現行管理者ベースとの比較・レポート生成 |
| `scripts/reevaluate_optimization_objectives.py` | GurobiのPWL近似結果を厳密な閉形式で再評価 |
| `scripts/generate_expected_contracts.py` / `plot_expected_contracts_svg.py` | 期待契約件数の系列生成・比較図 |
| `src/bundling_analysis/emarkov_estimator.py` | 劣化推移確率（マルコフ行列）の推定（MATLAB版`eMarkov.m`の移植） |
| `src/bundling_analysis/expected_contracts.py` | 補修確率q算出・閉形式期待契約件数関数。`DEFAULT_TRANSITION_MATRIX`はwith_supply系フル精度値 |
| `src/bundling_analysis/distance_cache.py` | 橋梁間距離（haversine）のSQLiteキャッシュ |
| `src/bundling_analysis/admin_boundary.py` | 行政界データ読込の統一ローダ |
| `src/bundling_analysis/preprocessing.py` | 和暦変換・緯度経度パース等の純粋関数 |
| `src/bundling_analysis/plotting_utils.py` | 日本語フォント設定など可視化の共通ユーティリティ |
| `src/bundling_analysis/config.py` | プロジェクト設定（`SHAPEFILE_PATH`, `I`(=L), `M_RANGE`等） |

Gurobiは別PC（ライセンス保有機）での実行を前提とする（`docs/gurobi_setup_log.md`, `docs/remote_gurobi_setup.md`）。実データでの通し実行・論文図表の再現は完了済み（`notes/step3_refactoring.md` 3c章）。地域分割最適化のフルグリッド（36ケース）再構築は進行中（同4章「残タスク」参照）。

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
- 補修確率: q ≈ 0.0123298（with_supply系、`src/bundling_analysis/expected_contracts.py`の`DEFAULT_TRANSITION_MATRIX`。中間審査pptxの数値と相対差5.4×10⁻⁶で一致確認済み）
- 同時発注上限: L = 5（基準値）、感度分析L = 1, 3, 7, 10
- 距離制約 D・地域数 M を政策変数として感度分析（本文主結果は全整数PWL、`data/processed/gurobi_validation_all_integer.csv`）

数値の根拠・複数系列の採否判断は `notes/pre_git_migration_inventory.md` を参照。
