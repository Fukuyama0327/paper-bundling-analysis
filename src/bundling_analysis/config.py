# -*- coding: utf-8 -*-
"""
設定ファイル - インフラ群マネジメント研究プロジェクト
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectConfig:
    """プロジェクト設定クラス。

    現行のステップ3パイプラインで実際に使うのは SHAPEFILE_PATH, I(=L),
    M_RANGE, GUROBI_THREADS, USE_PWL 程度。それ以外の多くは旧シミュレーション／
    旧目的関数（距離ペナルティ・類似性報酬・ワイブル劣化モデル等）由来のレガシーで、
    現行パイプラインでは未使用（notes/step3_refactoring.md 4章）。個々の項目末尾に
    「レガシー・現行未使用」を明記した。
    """
    # ファイルパス設定
    BRIDGE_DATA_FILE: str = "テスト宮城県橋梁位置.xlsx"  # レガシー・現行未使用（座標はx-Road原データから直接取得）
    SHAPEFILE_PATH: str = "data/N03-20230101_GML/N03-23_230101.shp"  # 現行使用（行政界クリップ）
    
    # シミュレーションパラメータ
    T: int = 100  # シミュレーション年数
    I: int = 5    # 一括発注あたりの上限橋梁数
    S: int = 10000  # シミュレーション回数
    
    # 目的関数パラメータ
    ALPHA_1: float = 1.6500e-3  # 距離ペナルティ係数（レガシー）
    ALPHA_2: float = 0.01       # 類似性報酬係数（レガシー）
    ALPHA_3: float = 1.0        # 劣化傾向ペナルティ係数（レガシー）
    
    # PDFレポート対応パラメータ
    MAX_DISTANCE_D: float = 50.0  # 地域内最大距離制約 [km]
    D_RANGE: tuple = (20, 100, 10)  # D値の範囲 (min, max, step)
    USE_SIMPLE_OBJECTIVE: bool = True  # PDFレポート形式（∑f(Nm)のみ）を使用するか
    
    # 機能のオプション設定
    USE_DEGRADATION_PENALTY: bool = False  # 劣化傾向ペナルティを使用するか
    USE_WEIBULL_MODEL: bool = False        # 2次元混合ワイブルモデルを使用するか（レガシー・現行未使用）
    USE_PEARSON_CORRELATION: bool = False  # ピアソン相関による類似度を使用するか
    
    # 劣化モデルパラメータ（レガシー・現行未使用。採用する劣化推移は
    # eMarkov 推定 → expected_contracts.DEFAULT_TRANSITION_MATRIX の系列）
    ALPHA: float = 1.2909       # 加速度パラメータ
    LOG_ETA: float = -5.1636    # ログスケールパラメータ
    VARPHI: float = 4.5534      # 異質性パラメータ
    
    # シード値
    SEED_SIMILARITY: int = 42   # 類似性行列用シード
    SEED_DEGRADATION: int = 123 # 劣化シミュレーション用シード
    
    # 最適化設定
    M_RANGE: tuple = (1, 7)     # 地域数の範囲 (start, end)
    N_SUBSET: int = 500          # 橋梁数の間引き設定
    
    # マルコフ遷移確率行列（レガシー・未使用の仮値）。
    # 採用する推移確率行列は expected_contracts.DEFAULT_TRANSITION_MATRIX
    # （with_supply系フル精度、q≈0.0123298）。名前が似ているが別物なので混同しないこと。
    MARKOV_TRANSITION_MATRIX = [
        [0.95, 0.05, 0.00],  # 状態1 → 状態1 or 2
        [0.00, 0.94, 0.06],  # 状態2 → 状態2 or 3
        [0.00, 0.00, 1.00]   # 状態3 → 状態3（固定）
    ]
    
    # 計算設定
    GUROBI_THREADS: int = 36    # Gurobiのスレッド数
    USE_PWL: bool = True        # 区分線形化の使用
    
    # Voronoi図設定
    MIN_POLYGON_AREA: float = 1e-6  # 最小ポリゴン面積（これより小さい領域は除外）
    
    # 出力設定
    OUTPUT_DIR_PREFIX: str = "results"
    FIGURE_SIZE: tuple = (12, 8)
    DPI: int = 150
    
    def __post_init__(self):
        """設定値の検証"""
        if self.T <= 0:
            raise ValueError("T (シミュレーション年数) は正の値である必要があります")
        if self.I <= 0:
            raise ValueError("I (一括発注上限) は正の値である必要があります")
        if self.S <= 0:
            raise ValueError("S (シミュレーション回数) は正の値である必要があります")
        if self.ALPHA_1 < 0:
            raise ValueError("ALPHA_1 (距離ペナルティ係数) は非負の値である必要があります")
        if self.ALPHA_2 < 0:
            raise ValueError("ALPHA_2 (類似性報酬係数) は非負の値である必要があります")
        if self.ALPHA_3 < 0:
            raise ValueError("ALPHA_3 (劣化傾向ペナルティ係数) は非負の値である必要があります")
    
    def get_eta(self) -> float:
        """指数変換されたetaパラメータを返す"""
        import numpy as np
        return np.exp(self.LOG_ETA)
    
    def get_markov_matrix(self) -> 'np.ndarray':
        """NumPy配列としてマルコフ遷移行列を返す"""
        import numpy as np
        return np.array(self.MARKOV_TRANSITION_MATRIX)
    
    def create_output_directory(self, subdir: str = "main") -> str:
        """タイムスタンプ付きの出力ディレクトリを作成

        Args:
            subdir: サブディレクトリ名 ("main", "hantei", "pref_data")
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y_%m%d%H%M")
        output_dir = f"results/{subdir}/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def save_config(self, output_dir: str) -> None:
        """設定をファイルに保存"""
        config_path = os.path.join(output_dir, "config.txt")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("=== プロジェクト設定 ===\n")
            f.write(f"T = {self.T}\n")
            f.write(f"I = {self.I}\n")
            f.write(f"S = {self.S}\n")
            f.write(f"ALPHA_1 = {self.ALPHA_1}\n")
            f.write(f"ALPHA_2 = {self.ALPHA_2}\n")
            f.write(f"ALPHA_3 = {self.ALPHA_3}\n")
            f.write(f"MAX_DISTANCE_D = {self.MAX_DISTANCE_D}\n")
            f.write(f"D_RANGE = {self.D_RANGE}\n")
            f.write(f"USE_SIMPLE_OBJECTIVE = {self.USE_SIMPLE_OBJECTIVE}\n")
            f.write(f"ALPHA = {self.ALPHA}\n")
            f.write(f"LOG_ETA = {self.LOG_ETA}\n")
            f.write(f"ETA = {self.get_eta()}\n")
            f.write(f"VARPHI = {self.VARPHI}\n")
            f.write(f"SEED_SIMILARITY = {self.SEED_SIMILARITY}\n")
            f.write(f"SEED_DEGRADATION = {self.SEED_DEGRADATION}\n")
            f.write(f"M_RANGE = {self.M_RANGE}\n")
            f.write(f"N_SUBSET = {self.N_SUBSET}\n")
            f.write(f"GUROBI_THREADS = {self.GUROBI_THREADS}\n")
            f.write(f"USE_PWL = {self.USE_PWL}\n")
            f.write("\n=== 機能オプション ===\n")
            f.write(f"USE_DEGRADATION_PENALTY = {self.USE_DEGRADATION_PENALTY}\n")
            f.write(f"USE_WEIBULL_MODEL = {self.USE_WEIBULL_MODEL}\n")
            f.write(f"USE_PEARSON_CORRELATION = {self.USE_PEARSON_CORRELATION}\n")

# デフォルト設定インスタンス
default_config = ProjectConfig()

def get_config() -> ProjectConfig:
    """設定オブジェクトを取得"""
    return default_config