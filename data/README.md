# data

論文の再現に必要な入力データの置き場所。

初期段階では、過去フォルダのデータをそのままコピーしない。まず、どの分析にどのデータが必要かを整理し、Git管理できるものだけを選別して追加する。

大きな生データや外部取得データは `data/raw/` または `data/external/` に置き、原則としてGit管理しない。

## processed

`data/processed/` には、論文中の図表再現に必要な小規模の派生データだけを置く。

現時点の管理対象:
- `expected_contracts_comparison_l5.csv`: \(L=5\) のシミュレーション値と閉形式解析解の比較。
- `expected_contracts_comparison_summary.csv`: \(L=1,3,5,7,10\) の比較誤差サマリー。
- `optimization_results_closed_form_20251207_200558.csv`: 閉形式目的関数による地域分割最適化結果。
- `optimization_results_supply_series_20251207_163046.csv`: 供給制約等を含む可能性がある差分調査用の最適化結果。
- `distance_matrix_322_20251208.pkl`: 別PCでGurobi再実行を行うための対象322橋梁の距離行列。
- `gurobi_validation_all_integer.csv`: 代表ケースを全整数PWLで再実行した検証結果。
- `gurobi_validation_20_nodes.csv`: 代表ケースを20点PWLで再実行した比較結果。
- `expected_contracts_matrix_n1-322.csv`: 期待契約件数 \(f(N,L)\)（\(N=1..322\), \(L=1,3,5,7,10\)）。`fig:expected_contracts` の一次再現元。中間審査pptxのchart4の外部リンク先 `20251126_中里さんから受領/expected_contracts_matrix.csv`（\(N=1..500\), \(L=1..50\) の完全テーブル）から転記したもので、\(N=322\) の値がpptx埋め込みチャートのキャッシュ値と一致することを確認済み（`notes/pre_git_migration_inventory.md` 0-5章）。
- `markov_input_20251207_200558/markov_input_*.txt`: eMarkov入力（4シナリオ）。`20251208_定期打ち合わせ/results/main/20251207_200558/simulation/` から転記した実データで、採用推移行列と同一実行のもの。`tab:transition_counts` と `fig:inspection_interval` の再現元（`scripts/make_transition_counts.py`, `scripts/plot_inspection_interval.py`）。
- `optimization_results_exact_objective.csv`: 20251207_200558系列の地域分割最適化結果を厳密な閉形式値で再評価したもの（`reevaluate_optimization_objectives.py`の出力）。`fig:optimization_results`・`tab:optimization_results`の入力（`scripts/plot_optimization_results.py`）。旧配置は`outputs/`だったがgit管理外だったため`data/processed/`へ移動（2026-07-11）。
- `target_rc_bridges_322.csv`: 対象6市町村のRC橋322件（`step3_extract_rc_bridges.py`→行政界チェック→`step3_filter_target_municipalities.py` の出力）。管理者別橋梁数（大河原町103・白石市98・蔵王町64・村田町33・川崎町14・七ヶ宿町10）から `tab:optimization_results` の管理者ベース基準値を計算する（`scripts/plot_optimization_results.py`）。注: 座標が福島県側にある「無名橋2号」（白石市管理）1件を行政界チェックで除外済み（これが歴史的なN=322 vs 323の差の正体）。

`optimization_results_closed_form_20251207_200558.csv` はGurobi最適化時のPWL近似値を含む。得られた地域分割を厳密な閉形式値で再評価する場合は `scripts/reevaluate_optimization_objectives.py` を使う。

`distance_matrix_322_20251208.pkl` は `scripts/run_gurobi_districting.py` の入力である。元の巨大データやNotebookを別PCへ持ち込まず、代表ケースのPWL検証を再実行するために管理する。

代表ケースの比較では、20点PWLと全整数PWLで \(D=35\) km, \(M=3\) の解が異なった。本文主結果は全整数PWLに寄せる。

出典:
- `20251126_中里さんから受領/output/`
- `20251208_定期打ち合わせ/results/main/`
