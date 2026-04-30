# Remote Gurobi Run Setup

このメモは、Gurobiが使える別PCで地域分割最適化を再実行するための手順である。

## 目的

査読論文で使う地域分割結果について、20点PWL近似と全整数PWLを比較し、PWL近似による解の妥当性を確認する。

まず確認する代表ケース:

```text
D=25km, M=3
D=35km, M=3
D=40km, M=1
```

## 必要なもの

- Python 3.10以上
- Gurobi本体
- 有効なGurobiライセンス
- このリポジトリ一式

このリポジトリには、再実行に必要な距離行列を含めている。

```text
data/processed/distance_matrix_322_20251208.pkl
```

これは `20251208_定期打ち合わせ/cache/dist_matrices/dist_322_77296b2021cf.pkl` をコピーしたもので、対象322橋梁の距離行列である。

## 初期設定

別PCでリポジトリを開いたら、仮想環境を作成する。

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

依存関係を入れる。

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[optimization]"
```

Gurobiの確認:

```bash
python -c "import gurobipy as gp; print(gp.gurobi.version())"
```

ここでエラーが出る場合は、Gurobi本体またはライセンス設定が未完了である。

## 代表ケースの実行

### 全整数PWL

まずはこちらを実行する。

```bash
python scripts/run_gurobi_districting.py ^
  --pwl all ^
  --cases 25:3 35:3 40:1 ^
  --threads 8 ^
  --output outputs/gurobi_validation_all_integer.csv ^
  --solutions-output outputs/gurobi_validation_all_integer_solutions.pkl
```

macOS / Linuxでは行継続を `\` にする。

```bash
python scripts/run_gurobi_districting.py \
  --pwl all \
  --cases 25:3 35:3 40:1 \
  --threads 8 \
  --output outputs/gurobi_validation_all_integer.csv \
  --solutions-output outputs/gurobi_validation_all_integer_solutions.pkl
```

### 20点PWL

比較用に、Notebookで使っていた20点PWLも実行する。

```bash
python scripts/run_gurobi_districting.py ^
  --pwl 20 ^
  --cases 25:3 35:3 40:1 ^
  --threads 8 ^
  --output outputs/gurobi_validation_20_nodes.csv ^
  --solutions-output outputs/gurobi_validation_20_nodes_solutions.pkl
```

## 出力

CSVには以下が出る。

- `MaxDistance`
- `M`
- `Status`
- `ObjectiveValue_PWL`
- `ObjectiveValue_Exact`
- `Difference_PWL_minus_Exact`
- `ElapsedSeconds`
- `RegionCounts`
- `PWLNodes`

論文上で重視するのは `ObjectiveValue_Exact` である。これは、得られた地域分割を厳密な閉形式 \(f(N,L)\) で再評価した値である。

## 判定基準

全整数PWLと20点PWLで以下を比較する。

- `RegionCounts` が同じか
- `ObjectiveValue_Exact` が同じか、または差が十分小さいか
- 実行時間が現実的か

全整数PWLで得られた解が20点PWLと同じであれば、本文では以下のように書ける。

```text
最適化では閉形式目的関数を区分線形化して解いた。
代表ケースにおいて全整数節点のPWLと20点PWLの結果を比較し、
20点PWLによる解が閉形式目的関数上でも同等であることを確認した。
```

差が出る場合は、全整数PWLの結果を主結果として採用する。

## 時間がかかる場合

まず `D=40km, M=1` を実行する。これは全橋梁を1地域にするケースなので短時間で終わるはずである。

```bash
python scripts/run_gurobi_districting.py --pwl all --cases 40:1 --threads 8
```

次に `D=35km, M=3`、最後に `D=25km, M=3` の順で試す。

時間が長すぎる場合は、一時的に制限を入れる。

```bash
python scripts/run_gurobi_districting.py ^
  --pwl all ^
  --cases 25:3 ^
  --threads 8 ^
  --time-limit 3600 ^
  --mip-gap 0.001
```

ただし、査読論文で「最適解」と書くには、最終的にはMIP gapを十分小さくする必要がある。
