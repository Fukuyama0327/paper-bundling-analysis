# -*- coding: utf-8 -*-
"""レガシー・シミュレーション比較検証用スクリプト（現行パイプライン未接続）。

補修契約件数をモンテカルロ・シミュレーションで並列計算する旧実装。import 時に
カレントディレクトリの ``input_data.pkl`` を前提とする設計で、現行のステップ3
パイプライン（`expected_contracts.py` の閉形式 f(N,L) を用いる系）には接続されて
おらず、README のパイプライン表にも掲載していない。閉形式解とシミュレーション値の
比較検証（`fig:expected_contracts` の系列）の出典として残している。
"""
import pickle  # オブジェクトの保存・読み込みに使用
import numpy as np  # 数値計算用
from tqdm import tqdm  # 進捗バーの表示用
from multiprocessing import Pool, cpu_count, Manager  # 並列処理用
import os
import sys
import logging

# ログ設定
LOG_LEVEL_NAME = os.getenv('PARALLEL_CONTRACTS_LOG_LEVEL', 'WARNING').upper()
FILE_LOG_LEVEL_NAME = os.getenv('PARALLEL_CONTRACTS_FILE_LOG_LEVEL', 'INFO').upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.WARNING)
FILE_LOG_LEVEL = getattr(logging, FILE_LOG_LEVEL_NAME, logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

file_handler = logging.FileHandler('parallel_contracts.log')
file_handler.setLevel(FILE_LOG_LEVEL)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(LOG_LEVEL)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.propagate = False

error_counter = None
error_counter_lock = None

# --- 入力データの読み込み ---
try:
    if not os.path.exists("input_data.pkl"):
        raise FileNotFoundError("入力データファイル 'input_data.pkl' が見つかりません")
    
    with open("input_data.pkl", "rb") as f:
        data = pickle.load(f)
    logger.info("入力データの読み込みが完了しました")
except Exception as e:
    logger.error(f"入力データの読み込みエラー: {e}")
    sys.exit(1)

# --- 入力データを変数に展開 ---
try:
    N_values = data["N_values"]               # 試行する橋梁数 N のリスト（1〜21）
    state_probs = data["state_probs"]         # 健全度1〜3の初期分布（確率）
    I = data["I"]                             # 契約件数の単位（I橋梁ごとに1件）
    P = data["P"]                             # マルコフ遷移行列（3×3）
    T = data["T"]                             # 計画期間（年）
    S = data["S"]                             # シミュレーション回数
    seed = data["seed"]                       # 乱数シード（再現性確保）
    
    # データの妥当性検証
    if not isinstance(N_values, list) or len(N_values) == 0:
        raise ValueError("N_values は空でないリストである必要があります")
    if not isinstance(state_probs, (list, np.ndarray)) or len(state_probs) != 3:
        raise ValueError("state_probs は長さ3の配列である必要があります")
    if not np.isclose(np.sum(state_probs), 1.0):
        raise ValueError("state_probs の合計は1.0である必要があります")
    if I <= 0 or T <= 0 or S <= 0:
        raise ValueError("I, T, S は正の値である必要があります")
    
    logger.info(f"パラメータ: N_values={len(N_values)}個, I={I}, T={T}, S={S}")
    logger.info(f"状態確率: {state_probs}")
    
except KeyError as e:
    logger.error(f"必要なキーが見つかりません: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"データ検証エラー: {e}")
    sys.exit(1)

# --- ワーカープロセス初期化 ---
def init_worker(counter, lock):
    global error_counter, error_counter_lock
    error_counter = counter
    error_counter_lock = lock

# --- 指定されたNについて契約件数をシミュレーションで推定 ---
def estimate_contracts_per_year(N):
    """
    指定された橋梁数Nに対して契約件数を推定する関数
    
    Args:
        N (int): 橋梁数
        
    Returns:
        tuple: (N, 年平均契約件数, 橋梁あたりの契約率)
    """
    try:
        if N <= 0:
            raise ValueError(f"橋梁数Nは正の値である必要があります: {N}")
        
        np.random.seed(seed + N * 1000)  # Nごとに異なるシード値を設定（衝突防止）

        result = np.zeros((S, T))  # S回×T年分の契約件数を記録する配列
        cumulative_P = np.cumsum(P, axis=1)  # マルコフ遷移確率の累積値（各行で使用）

        for s in range(S):
            cs = np.random.choice([1, 2, 3], size=N, p=state_probs)  # 初期健全度を確率に従って一括サンプル

            for t in range(T):
                result[s, t] = np.sum(cs == 3)  # 健全度3（要補修）の本数を記録
                cs = np.where(cs == 3, 1, cs)  # 補修済みの橋梁を健全度1にリセット

                if t < T - 1:
                    random_vals = np.random.rand(N)  # 次年度遷移判定用の乱数をまとめて生成
                    thresholds = cumulative_P[cs - 1]  # 現在の健全度ごとの累積遷移確率を取得
                    # 各橋梁で乱数がどの閾値を超えるかを数えることで次年度健全度を決定
                    cs = (random_vals[:, None] > thresholds).sum(axis=1) + 1

        R = result.reshape(-1)  # 全試行・全年度の契約件数を一次元に展開
        RR = np.ceil(R / I)  # 契約単位Iで切り上げて件数換算
        contracts_per_year = np.sum(RR) / (S * T)  # 年平均契約件数
        contracts_per_year_per_bridge = contracts_per_year / N  # 橋梁あたりの契約率

        # Nに対して契約件数・単位契約率を返す
        return (N, contracts_per_year, contracts_per_year_per_bridge)
        
    except Exception as e:
        error_message = f"{type(e).__name__}: {e}"
        logger.debug(f"N={N}のシミュレーションでエラー: {error_message}")
        if error_counter is not None and error_counter_lock is not None:
            with error_counter_lock:
                current = error_counter.get(error_message, 0)
                error_counter[error_message] = current + 1
        else:
            logger.error(f"N={N}のシミュレーションでエラー: {error_message}")
        return (N, 0, 0)  # エラー時はゼロを返す

# --- 並列処理ブロック（Main実行時のみ）---
if __name__ == "__main__":
    try:
        logger.info("並列処理を開始します")
        
        # 利用可能なCPU数を取得
        num_processes = min(cpu_count(), len(N_values))
        logger.info(f"使用プロセス数: {num_processes}")

        manager = Manager()
        shared_counter = manager.dict()
        shared_lock = manager.Lock()

        # 並列処理実行
        with Pool(processes=num_processes, initializer=init_worker, initargs=(shared_counter, shared_lock)) as pool:
            results = list(tqdm(
                pool.imap(estimate_contracts_per_year, N_values), 
                total=len(N_values),
                desc="シミュレーション実行中"
            ))

        # 結果の検証
        valid_results = [r for r in results if r[1] > 0]
        error_results = len(results) - len(valid_results)
        if error_results:
            logger.warning(f"警告: {error_results}個の結果でエラーが発生しました")

        aggregated_items = list(shared_counter.items())
        if aggregated_items:
            for message, count in sorted(aggregated_items, key=lambda item: item[1], reverse=True):
                logger.error(f"エラー {count}件: {message}")

        manager.shutdown()

        logger.info(f"シミュレーション完了: {len(valid_results)}/{len(results)}個の結果が有効")

        # 結果を出力ファイルに保存（pickle形式）
        output_file = "output_data.pkl"
        with open(output_file, "wb") as f:
            pickle.dump(results, f)

        logger.info(f"結果を {output_file} に保存しました")

        # 簡単な統計情報を出力
        if valid_results:
            contract_counts = [r[1] for r in valid_results]
            logger.info(f"契約件数統計: 最小={min(contract_counts):.3f}, 最大={max(contract_counts):.3f}, 平均={np.mean(contract_counts):.3f}")
        
    except Exception as e:
        logger.error(f"並列処理でエラー: {e}")
        sys.exit(1)
