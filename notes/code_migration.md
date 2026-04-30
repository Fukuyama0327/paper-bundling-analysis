# コード移植メモ

## 初回移植

参照元:
`/Users/fukuyamashunichi/Library/CloudStorage/OneDrive-個人用/02_東北大学/03_博士課程/2025FY/03_研究テーマ検討/20251208_定期打ち合わせ`

移植したファイル:
- `scripts/emarkov_estimator.py` -> `src/bundling_analysis/emarkov_estimator.py`
- `tools/distance_cache.py` -> `src/bundling_analysis/distance_cache.py`
- `config/config.py` -> `src/bundling_analysis/config.py`
- `scripts/parallel_contracts.py` -> `scripts/parallel_contracts.py`
- 閉形式の期待契約件数計算 -> `src/bundling_analysis/expected_contracts.py`

移植していないもの:
- `.venv/`
- `__pycache__/`
- `cache/`
- `data/`
- `results/`
- Notebook本体

## 次に確認すること

- `scripts/parallel_contracts.py` は現在 `input_data.pkl` をカレントディレクトリから読むため、論文用には引数指定型に直す。
- `config.py` は過去プロジェクトのパスやパラメータを含むため、論文で採用する設定だけに整理する。
- `distance_cache.py` は共有キャッシュへのパス探索を含むため、このリポジトリ内で完結する設定にするか判断する。
- Notebookで実施していた一連の分析は、再現可能なスクリプトに分解する。

## 閉形式関数の追加

`src/bundling_analysis/expected_contracts.py` には、以下を実装した。

- 推移確率行列 \(P\) から単一橋梁の補修確率 \(q\) を計算する関数。
- \(X \sim \mathrm{Binomial}(N,q)\) に対して \(E[\lceil X/L \rceil]\) を計算する関数。
- `compare_simulation_vs_formula.ipynb` の出力に基づくデフォルト推移確率行列。

確認:
- `python3 -m py_compile src/bundling_analysis/expected_contracts.py` は成功。
- `N=323, L=5` で期待契約件数は約 `1.194992` となり、`output/comparison_l=5.csv` の解析解と一致。
