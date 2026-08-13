# -*- coding: utf-8 -*-
"""論文図表の一括生成（非推奨・実行ごとのアーカイブ付き）。

非推奨（2026-08-13）: 本スクリプトが実行するのは図表スクリプトのうち一部だけで、
論文が使う図6点のうち3点（対象地域図・D-M感度図・地域内訳図・地域分割図）は作られない。
既定では `figures/`・`outputs/` の正本を更新するため、一部だけ新しく残りは古い、
という状態を作れてしまう。論文の図表を漏れなく作るには
`notebooks/pipeline_walkthrough.ipynb` の第6章を通して実行すること
（`docs/legacy_and_unused.md`）。

全図表生成スクリプトを一括実行し、成果物を2箇所に書き出す。

1. `outputs/runs/<タイムスタンプ>/` — 実行ごとのアーカイブ。上書きされない。
   実行ログ・引数・git HEADを `run.meta.json` に記録する。
2. `figures/`・`outputs/` — 正本（デフォルトで更新、`--no-canonical`で抑制）。
   main.texの`\\includegraphics`が参照する固定パスで、git管理なので
   上書きしてもコミット履歴から復元できる。

対象:
  - tab:transition_counts   (make_transition_counts.py)
  - fig:inspection_interval (plot_inspection_interval.py)
  - fig:optimization_results / tab:optimization_results (plot_optimization_results.py)
  - fig:expected_contracts_by_bundle_limit (plot_expected_contracts_by_limit.py)
  - fig:expected_contracts_scaling_analysis (plot_expected_contracts_scaling_analysis.py)

使用例:
    python scripts/make_all_figures.py                # アーカイブ＋正本更新
    python scripts/make_all_figures.py --no-canonical # アーカイブのみ（試行用）
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(script: str, args: list[str], log_dir: Path) -> dict:
    """図表生成スクリプトを1本実行し、ログを保存して結果を返す。"""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / script), *args]
    print(f"\n=== {script} ===")
    # 環境変数はまるごと引き継ぎ、PYTHONPATHだけ追記する。
    # 以前はPATH/PYTHONPATHをUnix向けの固定値で丸ごと差し替えていたため、
    # Windowsで USERPROFILE 等が消え、matplotlibがホームディレクトリを
    # 解決できずに落ちていた（2026-07-14に発見）。
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        src_path if not existing_pythonpath else f"{src_path}{os.pathsep}{existing_pythonpath}"
    )
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env,
    )
    sys.stdout.write(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
    (log_dir / f"{Path(script).stem}.log").write_text(
        result.stdout + ("\n--- stderr ---\n" + result.stderr if result.stderr else ""),
        encoding="utf-8",
    )
    return {"script": script, "args": args, "returncode": result.returncode}


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-canonical", action="store_true",
                        help="figures/・outputs/ の正本を更新せず、実行フォルダのみに出力する")
    parser.add_argument("--runs-root", type=Path, default=Path("outputs/runs"))
    args = parser.parse_args()

    print("警告: このスクリプトは図表スクリプトの一部しか実行しない（非推奨）。")
    print("      論文の図を漏れなく作るには notebooks/pipeline_walkthrough.ipynb 第6章を使う。")
    print("      作られない図: study_area / dm_sensitivity / region_breakdown / districting_map*\n")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = REPO_ROOT / args.runs_root / timestamp
    fig_dir = run_dir / "figures"
    tab_dir = run_dir / "tables"
    for d in (fig_dir, tab_dir):
        d.mkdir(parents=True, exist_ok=True)
    print(f"実行フォルダ: {run_dir}")

    steps = [
        ("make_transition_counts.py",
         ["--output", str(tab_dir / "transition_counts.csv")]),
        ("plot_inspection_interval.py",
         ["--output-stem", str(fig_dir / "inspection_interval")]),
        ("plot_optimization_results.py",
         ["--output-stem", str(fig_dir / "optimization_results"),
          "--table-output", str(tab_dir / "optimization_results_table.csv")]),
        ("plot_expected_contracts_by_limit.py",
         ["--output-stem", str(fig_dir / "expected_contracts_by_bundle_limit")]),
        # N=1000まで f(N,L) を全点評価するため1分弱かかる（他ステップより遅い）。
        ("plot_expected_contracts_scaling_analysis.py",
         ["--output-stem", str(fig_dir / "expected_contracts_scaling_analysis"),
          "--csv-output", str(tab_dir / "expected_contracts_scaling_analysis.csv")]),
    ]
    results = [run_step(script, step_args, run_dir) for script, step_args in steps]

    # 正本（figures/・outputs/）の更新: 実行フォルダからコピーする
    canonical_updated = []
    if not args.no_canonical:
        (REPO_ROOT / "figures").mkdir(exist_ok=True)
        for src in sorted(fig_dir.iterdir()):
            dst = REPO_ROOT / "figures" / src.name
            shutil.copy2(src, dst)
            canonical_updated.append(str(dst.relative_to(REPO_ROOT)))
        for name in ["transition_counts.csv", "optimization_results_table.csv",
                     "expected_contracts_scaling_analysis.csv"]:
            src = tab_dir / name
            if src.exists():
                dst = REPO_ROOT / "outputs" / name
                shutil.copy2(src, dst)
                canonical_updated.append(str(dst.relative_to(REPO_ROOT)))

    metadata = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_head": git_head(),
        "steps": results,
        "canonical_updated": canonical_updated,
    }
    with (run_dir / "run.meta.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    failed = [r["script"] for r in results if r["returncode"] != 0]
    print(f"\nアーカイブ: {run_dir}")
    if canonical_updated:
        print(f"正本更新: {len(canonical_updated)}ファイル（figures/・outputs/）")
    else:
        print("正本は更新していません（--no-canonical）")
    if failed:
        sys.exit(f"失敗したステップ: {failed}")
    print("全ステップ成功")


if __name__ == "__main__":
    main()
