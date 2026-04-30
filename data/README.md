# data

論文の再現に必要な入力データの置き場所。

初期段階では、過去フォルダのデータをそのままコピーしない。まず、どの分析にどのデータが必要かを整理し、Git管理できるものだけを選別して追加する。

大きな生データや外部取得データは `data/raw/` または `data/external/` に置き、原則としてGit管理しない。

## processed

`data/processed/` には、論文中の図表再現に必要な小規模の派生データだけを置く。

現時点の管理対象:
- `expected_contracts_comparison_l5.csv`: \(L=5\) のシミュレーション値と閉形式解析解の比較。
- `expected_contracts_comparison_summary.csv`: \(L=1,3,5,7,10\) の比較誤差サマリー。

出典:
`20251126_中里さんから受領/output/`
