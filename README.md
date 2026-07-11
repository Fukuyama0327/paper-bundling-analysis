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
  outline.md            # 章立て・構成メモ
  methodology.md        # モデル設計メモ
  results.md            # 数値計算結果メモ
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

Gurobiは別PC（ライセンス保有機）での実行を前提とする（`docs/gurobi_setup_log.md`, `docs/remote_gurobi_setup.md`）。実データでの通し実行はまだ実施しておらず、現状は合成データでの単体テストのみ（`notes/step3_refactoring.md` 4章「残タスク」参照）。

## 論文の構成（main.tex現状）

1. はじめに（群マネの背景・本研究の目的）
2. 既往研究（劣化モデル系 / 契約バンドリング系 / District Optimization系）
3. モデル構築（MIP定式化・マルコフ劣化モデル・閉形式期待契約件数関数）
4. 数値計算（宮城県RC橋、マルコフ推移確率推定・最適化結果）
5. 終わりに

## 研究ポジショニング（三研究群との対比）

| 研究群 | 補修需要の内生化 | 契約ロット設計 | 空間分割最適化 | 代表文献 |
|---|---|---|---|---|
| 劣化モデル系 | ○ | ✗ | ✗ | Hadjidemetriou 2020, Frangopol & Liu 2007 |
| 契約バンドリング系 | ✗（外生） | ○ | △ | Qiao 2018/2021, Miralinaghi 2022 |
| District Optimization系 | ✗ | ✗ | ○ | Kalcsics 2019, Bozkaya 2003 |
| **本研究** | **○** | **○** | **○** | 三系統の統合定式化 |

## 本研究の新規性（3点）

1. **問題設定**: 三研究群が断絶して発展してきた領域を一つの最適化問題として統合定式化
2. **方法論**: 点検データ→マルコフ遷移確率→補修需要確率→期待契約件数 という工学データから調達評価への接続パイプライン
3. **実証・政策**: 橋梁数・地域数・距離制約と期待契約件数の関係を実データで体系的に定量化

## 直近の作業状況

- `調達論点整理.md` 6章（既往研究・三系統レビュー＋DOIリンク）: 完了
- `調達論点整理.md` 7章（数理モデル全体像）: 完了
- `調達論点整理.md` 8章（新規性3点構成）: 完了
- `調達論点整理.md` 参考資料一覧（学術論文19件追加・タイトル検証済み）: 完了

## 主要パラメータ（数値計算）

- 対象: 宮城県内6市町村（七ヶ宿町・白石市・蔵王町・川崎町・村田町・大河原町）のRC橋 **322橋**（推移確率推定自体は宮城県内RC橋5,525橋のデータを使用）
- 補修確率: q ≈ 0.0123298（with_supply系、`src/bundling_analysis/expected_contracts.py`の`DEFAULT_TRANSITION_MATRIX`。中間審査pptxの数値と相対差5.4×10⁻⁶で一致確認済み）
- 同時発注上限: L = 5（基準値）、感度分析L = 1, 3, 7, 10
- 距離制約 D・地域数 M を政策変数として感度分析（本文主結果は全整数PWL、`data/processed/gurobi_validation_all_integer.csv`）

数値の根拠・複数系列の採否判断は `notes/pre_git_migration_inventory.md` を参照。
