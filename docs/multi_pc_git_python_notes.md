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

## 関連ドキュメント

- `docs/gurobi_setup_log.md`: Windows PCでのGurobi環境構築（`bridge-extract-gpu`環境の作成経緯）
- `docs/remote_gurobi_setup.md`: 別PCでの地域分割最適化の再実行手順
- `tests/test_step3_pipeline.py`: 合成データによるSTEP3の通しテスト（Gurobi不要、上記のPython 3.11環境で実行確認済み）
