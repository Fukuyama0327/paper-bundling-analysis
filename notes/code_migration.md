# コード移植メモ

## 初回移植

参照元:
`/Users/fukuyamashunichi/Library/CloudStorage/OneDrive-個人用/02_東北大学/03_博士課程/2025FY/03_研究テーマ検討/20251208_定期打ち合わせ`

移植したファイル:
- `scripts/emarkov_estimator.py` -> `src/bundling_analysis/emarkov_estimator.py`
- `tools/distance_cache.py` -> `src/bundling_analysis/distance_cache.py`
- `config/config.py` -> `src/bundling_analysis/config.py`
- `scripts/parallel_contracts.py` -> `scripts/parallel_contracts.py`

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

