# 複数PC（Mac / Windows）運用で詰まったこと・対処法

2026-07-06、Mac側でSTEP3リファクタリングをpushし、Windows PC（`C:\Users\shunf\paper-bundling-analysis`）でpull・合成テスト実行を行った際に発生した問題と対処法の記録。次回また同じ状況（複数PCでこのリポジトリを動かす）になったときに参照する。

## 1. Windows PC: Pythonバージョン不一致

`pyproject.toml`は`requires-python = ">=3.10"`だが、Windows PCのPowerShellで素の`pip`/`python`が指すPythonは3.9.13だった（`pip install -e ".[dev]"`が`ERROR: Package 'paper-bundling-analysis' requires a different Python: 3.9.13 not in '>=3.10'`で失敗）。

**確認済みの対処法**: 新しい環境を作る前に、既存のconda環境を確認する。

```powershell
C:\Users\shunf\anaconda3\condabin\conda.bat env list
```

このPCには以下が既にあった（2026-07-06時点）。

| 環境名 | Pythonバージョン | 備考 |
|---|---|---|
| `base` | 未確認 | `C:\Users\shunf\anaconda3` |
| `bridge-extract-gpu` | **3.11.15** | Gurobi検証用（`docs/gurobi_setup_log.md`）。**このリポジトリの`pip install -e ".[dev]"`にそのまま使える** |
| `geo_env` | 3.9.13 | 非対応 |
| `py37` | 3.7系 | 非対応 |

→ **`bridge-extract-gpu`を使うのが最短**。新規に`conda create`する必要はなかった。

## 2. `conda activate` が使えない（VS Code Remote等）

VS CodeのリモートターミナルやプレーンなPowerShellでは、`conda`コマンド自体が認識されない（Anaconda Promptを別途開く必要がある）。GUIでAnaconda Promptを開けない・開きたくない場合は、**`conda activate`を使わず、目的の環境のpython.exeをフルパスで直接呼ぶ**。

```powershell
C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe -m pip install -e ".[dev]"
C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe -m pytest tests/test_step3_pipeline.py -v
```

この方法はシェルの種類（VS Code統合ターミナル・SSHリモート・プレーンPowerShell等）に関係なく動く。`conda env list`だけは`condabin\conda.bat`をフルパスで呼べば`activate`なしでも実行できる。

## 3. PowerShellへの複数行貼り付けで行が連結される

複数のコマンドを別々のコードブロックとして順番に貼り付けると、前のコマンドの末尾と次のコマンドの先頭が改行なしで連結され、コマンドとして認識されないことがあった（例: `pytest tests/...-vC:\Users\shunf\anaconda3\condabin\conda.bat create...`のように混ざる）。

**対処法**: 複数コマンドを1回の操作で実行したい場合は、`;`で1行に連結した単一のコードブロックとして渡す。

```powershell
コマンド1; コマンド2; コマンド3
```

これなら貼り付け時の改行処理に依存しない。

## 4. Git pushで `HTTP 400` / `unexpected disconnect while reading sideband packet`

Mac側から`git push origin main`した際、大きめのpush（183オブジェクト、2.68MiB）で以下のエラーが出た。

```
error: RPC failed; HTTP 400 curl 22 The requested URL returned error: 400
send-pack: unexpected disconnect while reading sideband packet
fatal: the remote end hung up unexpectedly
```

**原因**: `http.postBuffer`のデフォルト値（1MiB）が小さすぎる、GitHub側でよくある問題。

**対処法**:

```bash
git config http.postBuffer 524288000
git push origin main
```

これで解決した（再pushで成功）。push前に`git fetch origin main`して`git rev-parse origin/main`と`HEAD`を比較すると、実際に反映されたかを確実に確認できる（`git push`の出力だけでは分かりにくいことがある）。

## 5. Git pullで `.git/objects/pack/*.idx` のunlink失敗プロンプト

Windows PCで`git pull`した際、以下の対話式プロンプトが出た。

```
Unlink of file '.git/objects/pack/pack-xxxx.idx' failed. Should I try again? (y/n)
```

**原因**: 別プロセス（エディタ、ウイルス対策ソフトのリアルタイムスキャン等）がそのファイルを掴んでいた可能性。

**対処法**: `y`で数回リトライしてダメなら`n`で進める（`n`を選んでも最終的に`Fast-forward`でpull自体は成功した）。リポジトリを開いているアプリを閉じてから再実行するとより確実。

## 6. Gurobiライセンス更新後も「期限切れ」エラーが出る

`grbgetkey`でライセンスを更新したのに古い期限切れエラーが出続けた。原因は`GRB_LICENSE_FILE`環境変数（Machineレベル）が`grbgetkey`のデフォルト保存先とは別の場所（このPCでは`C:\gurobi1000\gurobi.lic`）を指しており、新しいライセンス（`C:\Users\shunf\gurobi.lic`に保存）が読まれていなかったこと。診断・対処法は`docs/gurobi_setup_log.md` 12章に詳細を記載。

## 7. VS Code Remote経由の長時間計算がネットワーク切断で止まる

VS Code Remote（SSH・Tunnel等）の統合ターミナルで長時間かかるコマンド（例: 36ケースのGurobiフルグリッド実行）をそのまま実行すると、リモート接続が切れた時点でそのセッションに紐づくプロセスごと終了してしまう。バグではなく、接続とプロセスが親子関係にあるための仕様。

### 7-1. `Start-Process`（デタッチ実行）は不十分だった（2026-07-11〜12の実体験）

最初に試したのは、`Start-Process`でリモートセッションから切り離す方法。

```powershell
Start-Process -FilePath "C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe" `
  -ArgumentList "-u scripts\run_gurobi_districting.py --pwl all --cases 15:6 20:4 ... --threads 8 --output outputs\result.csv --solutions-output outputs\result_solutions.pkl" `
  -WorkingDirectory "C:\Users\shunf\paper-bundling-analysis" `
  -RedirectStandardOutput "outputs\run.log" -RedirectStandardError "outputs\run_error.log" `
  -NoNewWindow -PassThru
```

ポイント（`-u`＝unbuffered出力でログが即時反映される、`-WorkingDirectory`必須、`-PassThru`でプロセスID表示、`-NoNewWindow`でバックグラウンド化）は今も有効だが、**これだけでは不十分**だった。36ケースのフルグリッド実行で、**2回とも**エラーログ・例外なしに、Gurobiのログが突然途切れる形でプロセスが消えた（1回目は開始21分後・ギャップ20%、2回目は開始2.2時間後・ギャップ0.10%まで来ていた）。原因はスリープではない（`powercfg /change standby-timeout-ac 0`で無効化済みでも発生）。VS Code Remoteのセッション終了時に、`Start-Process`で作った子プロセスも何らかの経路で道連れにされている可能性が高いが、確証は得られていない。

**結論: `Start-Process`は「ターミナルを閉じる」対策にはなるが、「VS Code Remoteのセッション終了」対策としては信頼できなかった。**

### 7-2. 最終的な解決策: タスクスケジューラ（ログイン・リモート接続と完全に分離）

Windowsのタスクスケジューラにジョブとして登録すれば、ユーザーのログインセッション・リモート接続の生死と無関係に実行され続ける。パスワード保存が要らない`LogonType S4U`を使う。

```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c ""C:\Users\shunf\anaconda3\envs\bridge-extract-gpu\python.exe" -u scripts\run_gurobi_districting.py --pwl all --warm-start-min-m 4 --mip-gap 0.005 --cases 15:6 20:4 ... --threads 8 --output outputs\result.csv --solutions-output outputs\result_solutions.pkl > outputs\run.log 2> outputs\run_error.log"' -WorkingDirectory "C:\Users\shunf\paper-bundling-analysis"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(30)
$principal = New-ScheduledTaskPrincipal -UserId "<whoamiの出力>" -LogonType S4U -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 3) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "GurobiFullGrid" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
```

ポイント・ハマりどころ:

- **`-Execute`に直接python.exeを指定すると標準出力のリダイレクト（`>`）が効かない**（`New-ScheduledTaskAction`はシェルのリダイレクト構文を解釈しない）。`cmd.exe /c "実際のコマンド > log 2> errlog"`でラップする必要がある。
- **`-UserId "$env:USERDOMAIN\$env:USERNAME"`はエラーになった**（`Register-ScheduledTask : アカウント名とセキュリティ IDの間のマッピングは実行されませんでした`、HRESULT 0x80070534）。このPCでは`$env:USERDOMAIN`が正しく解決されていなかった。**`whoami`の生の出力（例: `desktop-qecoeiu\local_mizutani_1`）をそのまま`-UserId`に使ったら成功した。**
- 登録直後は`Register-ScheduledTask`の戻り値で`State: Ready`と表示されるだけで、実行が始まったかは別途確認が必要。
- `LogonType S4U`はネットワークドライブ等にはアクセスできないが、ローカルファイル操作のみのこのスクリプトには問題ない。

登録・起動確認:

```powershell
Get-ScheduledTask -TaskName "GurobiFullGrid" | Get-ScheduledTaskInfo
```

`LastRunTime`が直近なら起動済み。`LastTaskResult`が`267009`（0x41301）は「実行中」を表す正常値であってエラーではない。

進捗確認（プロセス・ログ・結果CSV）:

```powershell
Get-Process python -ErrorAction SilentlyContinue
Get-Content outputs\run.log -Tail 20
Get-Content outputs\result.csv
```

### 7-3. 合わせて使うと安心な追加策

- `--mip-gap 0.005`のように、ある程度のギャップ許容を付けておく。7-1の2回目の失敗は「あと少し（0.10%）で終わるところ」で消えたので、ギャップ許容があれば、その「あと少し」の時点で正常終了してCSVに書き込まれていた可能性が高い。全整数PWLなので、ギャップは近似ではなく本物の閉形式目的関数に対する保証。
- 難しいケース（M大きめ）だけ20点PWLの解を初期解として与える`--warm-start-min-m`（`scripts/run_gurobi_districting.py`に実装済み、`notes/step3_refactoring.md`参照）。

## 関連ドキュメント

- `docs/gurobi_setup_log.md`: Windows PCでのGurobi環境構築（`bridge-extract-gpu`環境の作成経緯）
- `docs/remote_gurobi_setup.md`: 別PCでの地域分割最適化の再実行手順
- `tests/test_step3_pipeline.py`: 合成データによるSTEP3の通しテスト（Gurobi不要、上記のPython 3.11環境で実行確認済み）
