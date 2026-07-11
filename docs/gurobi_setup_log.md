Gurobi検証用環境構築ログ（Windows GPU PC）

概要

本ドキュメントは、別PC（Windows）上でGurobiを用いた地域分割最適化検証を実行するための環境構築手順およびトラブル対応ログをまとめたものである。

最終的に以下が達成された：

* conda環境構築
* Gurobi本体との接続
* Pythonパッケージのインストール
* 検証スクリプト実行準備完了
* （※ライセンス期限切れで実行停止）

⸻

1. Python環境

使用環境

* Anaconda
* 仮想環境名：bridge-extract-gpu

conda activate bridge-extract-gpu

確認：

python -c "import sys; print(sys.executable)"
C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe

⸻

2. Gurobi本体の確認

既存インストールあり：

C:\gurobi1000
C:\gurobi952
C:\gurobi950

PATH追加：

set PATH=%PATH%;C:\gurobi1000\win64\bin

確認：

where.exe gurobi_cl
C:\gurobi1000\win64\bin\gurobi_cl.exe

⸻

3. gurobipy のインストール

バージョン整合のため明示指定：

pip install gurobipy==10.0.0

確認：

python -c "import gurobipy as gp; print(gp.gurobi.version())"
(10, 0, 0)

⸻

4. リポジトリのセットアップ

GitHubから取得：

git clone https://github.com/Fukuyama0327/paper-bundling-analysis.git
cd paper-bundling-analysis

Pythonパッケージとしてインストール：

python -m pip install -e ".[optimization]"

これにより以下が利用可能：

from bundling_analysis.expected_contracts import ...

⸻

5. 実行データ

以下ファイルが存在することを確認：

data/processed/distance_matrix_322_20251208.pkl

⸻

6. 検証スクリプト

実行コマンド（軽量ケース）：

python scripts/run_gurobi_districting.py ^
  --pwl all ^
  --cases 40:1 ^
  --threads 8 ^
  --output outputs/test.csv

⸻

7. 発生したエラーと対応

(1) ModuleNotFoundError

No module named 'bundling_analysis'

原因：

* editable install未実行

対応：

python -m pip install -e ".[optimization]"

⸻

(2) gurobipy DLLエラー

ImportError: DLL load failed

原因：

* Store版Python使用
* gurobipyと本体の不整合

対応：

* conda環境へ移行
* gurobipy==10.0.0 を再インストール

⸻

(3) 最終エラー（現在）

gurobipy.GurobiError: License expired

原因：

* Gurobiライセンス期限切れ

対応：

* 新しいライセンス取得
* grbgetkey 実行

⸻

8. 現在の状態（2026-07-06更新）

環境構築：完了
Gurobi接続：完了
スクリプト実行：可能
ライセンス：OK（2027-05-01まで、12章参照）
Python環境：`bridge-extract-gpu`（Python 3.11.15）をそのまま使用（詳細は`docs/multi_pc_git_python_notes.md`）

⸻

9. 次のステップ

1. ~~Gurobiライセンス更新~~ → 完了（12章）
2. 軽量ケース実行（D=40, M=1）
3. 代表ケース実行（D=25/35/40）
4. PWL比較（20点 vs 全整数）

⸻

12. ライセンス更新後もエラーが出た場合（2026-07-06に発生した問題と対処）

`grbgetkey`でライセンスを更新した**にもかかわらず**、`License expired <古い日付>`のエラーが出ることがある。

原因: `GRB_LICENSE_FILE`環境変数（システム環境変数、Machineレベル）が明示的に別のパスを指していると、`grbgetkey`のデフォルト保存先（`%USERPROFILE%\gurobi.lic`、このPCでは`C:\Users\shunf\gurobi.lic`）を無視して、`GRB_LICENSE_FILE`が指すファイルの方を読みに行く。

このPC（`C:\Users\shunf`）での実際の状況:
* `GRB_LICENSE_FILE`（Machine） = `C:\gurobi1000\gurobi.lic` ← Gurobiが実際に読むのはこちら
* `grbgetkey`のデフォルト保存先 = `C:\Users\shunf\gurobi.lic` ← 新しいライセンスはこちらに保存される

つまり、`grbgetkey`を実行しても`GRB_LICENSE_FILE`が指す方のファイルは自動更新されない。

診断コマンド（新しいライセンス取得後、まずこれを実行して場所のズレがないか確認する）:

```powershell
Write-Host "Machine: $([Environment]::GetEnvironmentVariable('GRB_LICENSE_FILE','Machine'))"
Get-ChildItem -Path "C:\Users\shunf","C:\gurobi1000","C:\gurobi952","C:\gurobi950" -Filter "gurobi.lic" -Recurse -ErrorAction SilentlyContinue -Force | ForEach-Object {
    Write-Host "--- $($_.FullName) (更新: $($_.LastWriteTime)) ---"
    Get-Content $_.FullName | Select-String -Pattern "EXPIRATION"
}
```

対処（`GRB_LICENSE_FILE`が指す場所へ、新しいライセンスの中身を上書きコピーする。環境変数自体は変更しないので即座に反映される）:

```powershell
Copy-Item "C:\Users\shunf\gurobi.lic" "C:\gurobi1000\gurobi.lic" -Force
```

確認:

```powershell
C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe -c "import gurobipy as gp; m = gp.Model(); print('gurobi ok')"
```

`Academic license - for non-commercial use only - expires <日付>` と `gurobi ok` が出れば解決。次回ライセンス更新時は、`grbgetkey`実行後に必ずこの診断コマンドで場所のズレがないか確認すること。

⸻

10. 補足（重要な設計判断）

* Gurobiは PWL近似で最適化
* 評価は 閉形式で再計算
* 検証は 全整数PWLとの比較で担保

⸻

結論

本環境は、ライセンス更新後すぐにGurobi検証が実行可能な状態に到達している。

⸻

11. ライセンス更新手順

新しい Gurobi ライセンスキーを取得済み。

重要:

* ライセンスキーはGit管理しない
* `gurobi.lic` もGit管理しない
* キーをこのメモに書かない

Windows GPU PC側で、Anaconda Prompt または PowerShell を開き、以下を実行する。

```bat
conda activate bridge-extract-gpu
set PATH=%PATH%;C:\gurobi1000\win64\bin
grbgetkey <取得したライセンスキー>
```

`grbgetkey` 実行時に保存先を聞かれた場合は、通常はデフォルトのユーザーディレクトリでよい。

典型例:

```text
C:\Users\shunf\gurobi.lic
```

ライセンス確認:

```bat
gurobi_cl
```

Pythonからの確認:

```bat
python -c "import gurobipy as gp; m = gp.Model(); print('gurobi ok')"
```

ここまで通ったら、軽量ケースを実行する。

```bat
python scripts/run_gurobi_districting.py ^
  --pwl all ^
  --cases 40:1 ^
  --threads 8 ^
  --output outputs/gurobi_validation_all_integer_D40M1.csv
```

期待する確認点:

* `Status` が最適解または少なくとも解あり
* `RegionCounts` が `322`
* `ObjectiveValue_Exact` が `1.193288279181` 付近

その後、代表ケースを実行する。

```bat
python scripts/run_gurobi_districting.py ^
  --pwl all ^
  --cases 25:3 35:3 40:1 ^
  --threads 8 ^
  --output outputs/gurobi_validation_all_integer.csv ^
  --solutions-output outputs/gurobi_validation_all_integer_solutions.pkl
```

比較用に20点PWLも実行する。

```bat
python scripts/run_gurobi_districting.py ^
  --pwl 20 ^
  --cases 25:3 35:3 40:1 ^
  --threads 8 ^
  --output outputs/gurobi_validation_20_nodes.csv ^
  --solutions-output outputs/gurobi_validation_20_nodes_solutions.pkl
```
