# 現行パイプラインから外れているコード

論文の図表生成には繋がっていないが、リポジトリに残してあるものの一覧。
「動くが触らなくてよい」ことを明示しておくための文書。

| 対象 | 状態 | 理由 |
|---|---|---|
| `scripts/parallel_contracts.py` | レガシー | シミュレーション比較用。閉形式 vs モンテカルロの比較図は論文から廃止済み |
| `scripts/generate_expected_contracts.py` | 補助 | \(f(N,L)\) の系列CSVを出力するだけ。図は各 `plot_*` が直接計算するので図表生成には不要 |
| `scripts/extract_pdf_text.py` | 補助 | 参考文献PDFのテキスト抽出。分析パイプラインとは無関係 |
| `scripts/step3_compare_and_report.py` | 任意 | 管理者ベース比較の詳細レポート。本文の基準値は `plot_optimization_results.py` 側で計算する |
| `src/bundling_analysis/config.py` | 上流で一部のみ使用 | `step3_extract_rc_bridges.py` が `SHAPEFILE_PATH` を取るためだけに import する。`I`(=L) や `M_RANGE` 等は**どこからも読まれておらず**、実効値は各CLIの引数側 |
| `src/bundling_analysis/preprocessing.py` / `distance_cache.py` | 上流専用 | 対象橋梁の抽出・距離行列の構築でのみ使用。図表生成では呼ばれない |
| `scripts/make_all_figures.py` | 非推奨 | 図表スクリプトのうち5本しか実行せず、論文の図6点のうち3点（対象地域図・D-M感度図・地域内訳図・地域分割図）を作らない。それでいて既定で正本を上書きするため、一部だけ新しい状態を作れてしまう。図表生成は `notebooks/pipeline_walkthrough.ipynb` 第6章に一本化した（2026-08-13） |

確認方法:

```bash
# config.py を import しているファイル（step3_extract_rc_bridges.py の1本だけのはず）
grep -rl --include=*.py "bundling_analysis.config" scripts src tests

# config.I（＝L）を読んでいる箇所（無いはず）
grep -rn --include=*.py "get_config()\.I\|config\.I\b" scripts src
```

## 履歴から外したデータ

| 対象 | 経緯 |
|---|---|
| `data/processed/optimization_results_closed_form_20251207_200558.csv` | 20251207_200558実行の結果（PWL近似値を含む旧系列）。正本 `optimization_results_exact_objective.csv` の再生成元ではなく、参照するコードも無かったため2026-08-13に管理対象から外した。git履歴には残っており `git show <commit>:<path>` で取り出せる |
