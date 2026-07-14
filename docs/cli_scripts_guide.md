# CLIスクリプトの使い方ガイド（Jupyter Notebookから来た人向け）

このリポジトリの`scripts/`配下は、Jupyter Notebookのように「セルを上から順に実行して、変数を書き換えて再実行する」のではなく、ターミナルから**コマンドとオプションを指定して1回実行する**形式（CLI: コマンドラインインターフェース）になっている。この文書は、その基本と、このリポジトリの各スクリプトの実際の使い方をまとめたもの。

## 1. 基本の考え方

Notebookでは、セルの中で直接こう書いていた。

```python
D = 25
M = 3
threads = 8
# ...セルを実行...
```

CLIスクリプトでは、この「変数への代入」の代わりに、実行時にコマンドの後ろへ`--変数名 値`という形で渡す。

```powershell
python scripts\run_gurobi_districting.py --threads 8
```

これは「`run_gurobi_districting.py`を実行し、`threads`という設定に`8`を渡す」という意味。`--threads`のような`--`で始まる部分を**オプション（フラグ）**と呼ぶ。

### なぜこの形式なのか

- Notebookのようにセルの実行順序に依存しない（毎回、必要な設定を全部その場で渡すので再現しやすい）
- 別PC（Windows）で動かすときも、同じコマンドをコピペするだけで済む
- 実行結果を変えたいとき、コードを書き換えずに済む（値だけ変える）

## 2. オプションの基本パターン

### 2-1. 値を1つ渡すオプション

```powershell
python scripts\step3_filter_target_municipalities.py --input data\processed\miyagi_rc_bridges.csv --output data\processed\target_rc_bridges_322.csv
```

`--input`の後ろの値がファイルパス、`--output`の後ろの値が出力先。**1つのオプションと1つの値がセット**になっている。順番はどちらが先でもよい。

### 2-2. 複数の値を渡すオプション（`nargs="+"`）

`run_gurobi_districting.py`の`--cases`は、複数の値をまとめて渡せる特殊なオプション。

```powershell
python scripts\run_gurobi_districting.py --cases 25:3 35:3 40:1
```

これは「`--cases`に、`25:3`と`35:3`と`40:1`という3つの値のリストを渡す」という意味。`25:3`は「距離制約D=25km、地域数M=3」を`D:M`という書式でまとめたもの（このスクリプト独自の書式で、`scripts/run_gurobi_districting.py`内の`parse_case`関数がこの文字列を解釈している）。空白区切りで好きなだけケースを並べられる。

```powershell
# 3ケースだけ
python scripts\run_gurobi_districting.py --cases 25:3 35:3 40:1

# 36ケース全部（フルグリッド）
python scripts\run_gurobi_districting.py --cases 15:6 20:4 20:5 20:6 25:3 25:4 25:5 25:6 30:2 30:3 30:4 30:5 30:6 35:2 35:3 35:4 35:5 35:6 40:1 40:2 40:3 40:4 40:5 40:6 45:1 45:2 45:3 45:4 45:5 45:6 50:1 50:2 50:3 50:4 50:5 50:6
```

### 2-3. 選択肢から選ぶオプション（`choices=[...]`）

`--pwl`は`"all"`か`"20"`のどちらかしか受け付けない。

```powershell
python scripts\run_gurobi_districting.py --pwl all   # 全整数PWL
python scripts\run_gurobi_districting.py --pwl 20    # 20点PWL
```

それ以外の値（例: `--pwl 15`）を渡すとエラーになる。

### 2-4. 指定しなくてもよいオプション（デフォルト値がある）

ほとんどのオプションには初期値（デフォルト）が設定されているので、変えたいものだけ指定すればよい。例えば`run_gurobi_districting.py`は`--distance-matrix`を指定しなければ自動的に`data/processed/distance_matrix_322_20251208.pkl`を使う。

## 3. 「このスクリプト、どんなオプションがあるんだっけ？」を調べる方法

どのスクリプトも、末尾に`--help`（または`-h`）を付けて実行すると、受け付けるオプション一覧と説明が表示される。**まずこれを打てば、スクリプトのソースコードを読まなくても使い方がわかる。**

```powershell
python scripts\run_gurobi_districting.py --help
```

## 4. このリポジトリの主要スクリプト一覧

### `scripts/run_gurobi_districting.py`（地域分割最適化、Gurobi必須）

| オプション | 意味 | デフォルト |
|---|---|---|
| `--distance-matrix` | 距離行列pklのパス | `data/processed/distance_matrix_322_20251208.pkl` |
| `--cases` | `D:M`形式のケースを空白区切りで複数指定 | `25:3 35:3 40:1` |
| `--pwl` | `all`（全整数）または`20`（20点近似） | `all` |
| `--bundle-limit` | 契約バンドリング上限L | `5` |
| `--threads` | Gurobiのスレッド数（0でデフォルト） | `0` |
| `--time-limit` | 1ケースあたりの制限時間（秒） | 制限なし |
| `--mip-gap` | 許容MIPギャップ | Gurobiデフォルト |
| `--output` | 結果CSVの出力先 | `outputs/gurobi_districting_validation.csv` |
| `--solutions-output` | 割当行列pklの出力先 | `outputs/gurobi_districting_validation_solutions.pkl` |

例（代表3ケース、全整数PWL）:

```powershell
python scripts\run_gurobi_districting.py --pwl all --cases 25:3 35:3 40:1 --threads 8 --output outputs\result.csv --solutions-output outputs\result_solutions.pkl
```

### `scripts/step3_extract_rc_bridges.py`（x-Road原データ→RC橋抽出）

| オプション | 意味 |
|---|---|
| `--input` | x-Road原データCSV（必須） |
| `--output` | 出力CSVパス（必須） |
| `--prefecture` | 対象都道府県名（デフォルト`宮城県`） |
| `--boundary` | 行政界シェープファイル（省略時は`config.SHAPEFILE_PATH`。県境界外を除外） |
| `--no-boundary` | 行政界チェックをスキップ（県外座標の橋梁が残りN=322が再現できなくなるため、意図的な場合のみ） |

### `scripts/step3_filter_target_municipalities.py`（6市町村フィルタ、N=322）

| オプション | 意味 |
|---|---|
| `--input` | RC橋CSV（必須、`step3_extract_rc_bridges.py`の出力） |
| `--output` | 出力CSVパス（必須） |

### `scripts/step3_prepare_markov_input.py`（eMarkov入力整形）

| オプション | 意味 |
|---|---|
| `--rc-bridges` | RC橋CSV（必須） |
| `--maintenance` | 施設番号付与済み道路メンテナンス年報CSV（必須） |
| `--output-dir` | eMarkov入力TSVの出力ディレクトリ（必須。4シナリオ分のファイルがまとめて出力される） |

### `scripts/step3_build_distance_matrix.py`（距離行列構築）

| オプション | 意味 |
|---|---|
| `--input` | 対象橋梁CSV（必須、`shisetsu_id`・緯度・経度列が必要） |
| `--output` | 出力pklパス（必須） |
| `--db-path` | `dist_cache.sqlite`のパス（省略時はデフォルト位置） |

### `scripts/step3_compare_and_report.py`（管理者ベースとの比較）

| オプション | 意味 |
|---|---|
| `--bridges` | 対象橋梁CSV（必須、管理者列が必要） |
| `--distance-matrix` | 距離行列pkl（必須） |
| `--solutions` | 最適化割当pkl（必須、`run_gurobi_districting.py`の`--solutions-output`） |
| `--bundle-limit` | 契約バンドリング上限L（デフォルト5） |
| `--output` | 比較結果CSVの出力先（必須） |

### `scripts/reevaluate_optimization_objectives.py`（PWL結果を閉形式で再評価）

| オプション | 意味 |
|---|---|
| `--input` | Gurobi結果CSV（デフォルト`data/processed/optimization_results_closed_form_20251207_200558.csv`） |
| `--output` | 再評価後CSVの出力先（デフォルト`data/processed/optimization_results_exact_objective.csv`。`plot_optimization_results.py`のデフォルト入力と同一パス） |
| `--bundle-limit` | 契約バンドリング上限L（デフォルト5） |

### `scripts/generate_expected_contracts.py`（期待契約件数の系列生成）

| オプション | 意味 |
|---|---|
| `--max-n` | 最大橋梁数N（デフォルト323） |
| `--bundle-limits` | Lの候補を複数指定（`--cases`と同じ書式、空白区切り） |
| `--output` | 出力先 |

### `scripts/plot_expected_contracts_svg.py`（比較図の生成）

| オプション | 意味 |
|---|---|
| `--input` | 入力データ |
| `--output` | 出力SVGパス |

## 5. Windows PowerShell特有の注意

- コマンドは**1行で完結させて貼り付ける**。複数行に分けて別々に貼ると、前の行の末尾と次の行の先頭が連結されて壊れることがある（`docs/multi_pc_git_python_notes.md` 3章参照）。
- 複数コマンドをまとめて1回で実行したいときは`;`で繋ぐ。
- `conda activate`が使えない場合は、目的の環境の`python.exe`をフルパスで直接呼べばよい（`docs/multi_pc_git_python_notes.md` 2章参照）。

```powershell
C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe scripts\run_gurobi_districting.py --help
```
