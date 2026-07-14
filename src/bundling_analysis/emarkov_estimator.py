"""MATLAB 版 eMarkov.m を Python に移植した実装モジュール。

現在の所在は ``src/bundling_analysis/emarkov_estimator.py``。パイプラインからは
``scripts/step3_run_emarkov.py`` 経由で呼び出す。このモジュールを直接
``python -m bundling_analysis.emarkov_estimator`` として実行すると、MATLAB と同じ
入力（NationalRoadDB.txt）に対して同じ指標が得られる（末尾の ``__main__`` デモ）。

元の MATLAB コードはニュートン–ラフソン法で多段階の劣化マルコフ
モデルを推定する。ここでは同じアルゴリズムを Python/Numpy で再現し、
pandas データフレームなど任意の入力形式から推定できるよう整備している。

主な変更点は次のとおり。
    * MATLAB の列優先と Python の行優先の違いを吸収するため、
      設計行列は (n_samples, n_features) で受け取り内部で転置する。
    * 説明変数が無い場合でも切片のみのモデルとして推定できる。
    * 0 除算を避けるための小さな値（1e-12）を適宜挿入し、
      MATLAB で暗黙的に処理されていた数値不安定を抑えている。

MATLABとの完全一致を目指す場合の推奨設定::

    >>> est = EMarkovEstimator(
    ...     max_iter=100,
    ...     tol=1e-6,
    ...     matlab_convergence=True,      # MATLAB方式の収束判定
    ...     scaling_method="max",         # MATLAB互換のスケーリング
    ...     final_iter_no_ridge=3,        # 最終3反復で正則化OFF
    ...     verbose=True,                 # 反復ログを表示
    ...     ll_epsilon=1e-300,            # LL計算の下駄
    ... )
    >>> # 初期値とマスクもMATLABに合わせる
    >>> result = est.fit(
    ...     before, after, interval, X,
    ...     initial_beta=matlab_XB,       # MATLABの初期ベクトル
    ... )

代表的な利用方法::

    >>> import pandas as pd
    >>> df = pd.read_csv("...prefecture_data...")
    >>> from bundling_analysis.emarkov_estimator import (
    ...     prepare_transition_arrays,
    ...     build_design_matrix,
    ...     EMarkovEstimator,
    ... )
    >>> before, after, interval = prepare_transition_arrays(df)
    >>> X, scales = build_design_matrix(before.size, feature_values=None)
    >>> est = EMarkovEstimator()
    >>> result = est.fit(before, after, interval, X)
    >>> print(result.beta_matrix)

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

import json
import os

import numpy as np

# pandas は DataFrame 入力を扱う際のみ必要なので、存在チェックを挟む
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - pandas is optional
    pd = None  # type: ignore


@dataclass
class EMarkovResult:
    """推定結果を保持するデータクラス。MATLAB で disp していた値を整理。"""

    beta_matrix: np.ndarray
    t_values: np.ndarray
    hazards: np.ndarray
    transition_matrix: np.ndarray
    log_likelihood: float
    aic: float
    iterations: int
    error: float
    beta_flat: np.ndarray
    feature_scales: np.ndarray


class EMarkovEstimator:
    """ニュートン–ラフソン法で劣化マルコフモデルを推定するメインクラス。"""

    # step3_run_emarkov.py（およびこのモジュールの __main__ デモ）は
    # このクラスで MATLAB の eMarkov.m と同じ推定を行う

    def __init__(
        self,
        max_iter: int = 100,
        tol: float = 1e-6,
        parameter_mask: Optional[Sequence[bool]] = None,
        ridge_lambda: float = 1e-8,
        final_iter_no_ridge: int = 3,
        matlab_convergence: bool = True,
        verbose: bool = False,
        scaling_method: str = "max",
        ll_epsilon: float = 1e-300,
    ) -> None:
        """
        Parameters
        ----------
        max_iter : int
            最大反復回数
        tol : float
            収束判定の閾値
        parameter_mask : sequence of bool, optional
            推定するパラメータのマスク（True=推定、False=固定0）
        ridge_lambda : float
            ヘッセ行列の正則化係数
        final_iter_no_ridge : int
            最終何反復で正則化をOFFにするか（0=常にON）
        matlab_convergence : bool
            True=MATLAB方式の収束判定（分母に下駄なし）
        verbose : bool
            反復ログを出力するか
        scaling_method : str
            "max" (MATLAB互換) or "maxabs" (Python既存)
        ll_epsilon : float
            LL計算時の確率下限（log(0)回避用）
        """
        self.max_iter = max_iter
        self.tol = tol
        self.parameter_mask = parameter_mask
        self.ridge_lambda = ridge_lambda
        self.final_iter_no_ridge = final_iter_no_ridge
        self.matlab_convergence = matlab_convergence
        self.verbose = verbose
        self.scaling_method = scaling_method  # "maxabs" or "max"
        self.ll_epsilon = ll_epsilon

    def fit(
        self,
        before: Sequence[int],
        after: Sequence[int],
        interval: Sequence[float],
        design_matrix: np.ndarray,
        initial_beta: Optional[Sequence[float]] = None,
        x_eval: Optional[Sequence[float]] = None,
        z_eval: float = 1.0,
    ) -> EMarkovResult:
        """モデルパラメータを推定する。

        Parameters
        ----------
        before, after : array-like
            点検前後の段階（1 始まりのカテゴリ値）。
        interval : array-like
            点検間隔（年）。
        design_matrix : ndarray
            説明変数行列。必要なら切片列を含める。
        initial_beta : sequence, optional
            ニュートン法の初期値。省略時は段階ごとに減少する切片を設定。
        x_eval : sequence, optional
            収束後にハザード・推移確率を評価する説明変数ベクトル。
        z_eval : float, default 1.0
            推移確率評価に用いる経過年数。
        """

        before = np.asarray(before, dtype=int)
        after = np.asarray(after, dtype=int)
        interval = np.asarray(interval, dtype=float)
        if design_matrix.ndim != 2:
            raise ValueError("design_matrix must be 2D (n_samples, n_features)")

        n_samples, n_features = design_matrix.shape
        if before.shape[0] != n_samples or after.shape[0] != n_samples:
            raise ValueError("before/after must align with design_matrix rows")

        if np.any(after < 1):
            raise ValueError("Stage codes must be 1-indexed positive integers")

        jmax = int(after.max())  # MATLAB の段階数 Jmax
        if jmax < 2:
            raise ValueError("Need at least two stages for Markov transitions")

        design = design_matrix.T.copy()  # MATLAB の列優先行列と整合させる
        # スケーリング方法を選択（MATLAB互換性のため）
        scales = np.ones(design.shape[0])
        for idx in range(design.shape[0]):
            row = design[idx]
            if self.scaling_method == "max":
                # MATLABの max(rXk(i,:)) 方式
                max_val = np.nanmax(row)
            else:
                # 既存の max(abs(row)) 方式
                max_val = np.nanmax(np.abs(row))
            if not np.isfinite(max_val) or max_val == 0:
                max_val = 1.0
            design[idx] = row / max_val
            scales[idx] = max_val

        n_params = (jmax - 1) * n_features  # MATLAB での XB 長さに相当
        if initial_beta is None:
            # MATLAB 互換ノートブック（emarkov_yn）の初期値に合わせて強めの負の切片を入れる
            # （-0.5 刻みだと収束が遅いケースがあるため、ステージごとに -2,-4,... とする）
            intercept_init = -2.0 * np.arange(1, jmax)
            beta_default = np.zeros((jmax - 1, n_features), dtype=float)
            if n_features > 0:
                beta_default[:, 0] = intercept_init
            beta_flat = beta_default.reshape(-1)
        else:
            beta_flat = np.asarray(initial_beta, dtype=float).copy()
            if beta_flat.size != n_params:
                raise ValueError(
                    f"initial_beta must have {(jmax - 1) * n_features} entries, "
                    f"got {beta_flat.size}"
                )

        mask = self._build_parameter_mask(n_params)
        beta_flat = beta_flat.reshape(-1)
        active_idx = np.where(mask)[0]
        inactive_idx = np.where(~mask)[0]
        beta_active = beta_flat[active_idx]

        errors = []
        log_likelihoods = []

        for iteration in range(1, self.max_iter + 1):
            grad = np.zeros_like(beta_flat)
            hess = np.zeros((n_params, n_params), dtype=float)

            for k in range(n_samples):
                self._accumulate_sample_terms(
                    grad,
                    hess,
                    before[k],
                    after[k],
                    interval[k],
                    design[:, k],
                    beta_flat,
                    jmax,
                    n_features,
                )

            # 不活性パラメータを取り除いて線形方程式を解く（MATLAB の DL 処理と同じ）
            grad_active = grad[active_idx]
            hess_active = hess[np.ix_(active_idx, active_idx)]

            # 正則化の調整（最終段階ではOFFに）
            if self.final_iter_no_ridge > 0 and iteration > self.max_iter - self.final_iter_no_ridge:
                ridge = 0.0
            else:
                ridge = self.ridge_lambda

            hess_active_reg = hess_active + np.eye(hess_active.shape[0]) * ridge
            step = np.linalg.solve(hess_active_reg, grad_active)
            beta_new_active = beta_active - step

            beta_flat[active_idx] = beta_new_active
            beta_flat[inactive_idx] = 0.0

            # 収束判定: MATLAB方式 vs Python方式
            if self.matlab_convergence:
                # MATLAB: Er(ii) = max(abs((MXB - XB)./MXB))
                # 分母は新しい値（MXB）のみ、下駄なし
                with np.errstate(divide='ignore', invalid='ignore'):
                    rel_diffs = np.abs(beta_new_active - beta_active) / np.abs(beta_new_active)
                    rel_diffs = np.where(np.isfinite(rel_diffs), rel_diffs, 0.0)
                rel_error = np.max(rel_diffs) if rel_diffs.size > 0 else 0.0
            else:
                # Python既存方式: 下駄あり
                rel_error = np.max(
                    np.abs(beta_new_active - beta_active)
                    / np.maximum(np.abs(beta_new_active), 1e-12)
                )

            errors.append(rel_error)

            # ログ出力（verbose=True時）
            if self.verbose:
                beta_matrix_temp = beta_flat.reshape((jmax - 1), n_features)
                ll = self._compute_log_likelihood(before, after, interval, design, beta_matrix_temp)
                log_likelihoods.append(ll)
                grad_norm = np.linalg.norm(grad_active, np.inf)
                step_norm = np.linalg.norm(step, np.inf)
                print(f"Iter {iteration:3d}: LL={ll:12.6f}, ||grad||_∞={grad_norm:10.3e}, "
                      f"||step||_∞={step_norm:10.3e}, rel_err={rel_error:10.3e}, ridge={ridge:.1e}")

            beta_active = beta_new_active

            if rel_error < self.tol:
                break
        else:
            iteration = self.max_iter  # 収束に到達しなかった場合

        beta_matrix = beta_flat.reshape((jmax - 1), n_features)

        # t 値（収束後のヘッセ行列を用いて算出）
        hess_active = hess[np.ix_(active_idx, active_idx)]  # MATLAB の HE を縮退
        hess_active_reg = hess_active + np.eye(hess_active.shape[0]) * 1e-8
        fisher_info = -np.linalg.inv(hess_active_reg)  # 収束後のフィッシャー情報（MATLAB FH）
        t_values = np.zeros_like(beta_flat)
        diag = np.sqrt(np.clip(np.diag(fisher_info), a_min=1e-12, a_max=None))
        t_values[active_idx] = beta_active / diag
        t_values_matrix = t_values.reshape((jmax - 1), n_features)

        x_eval_vec = np.ones(n_features) if x_eval is None else np.asarray(x_eval, dtype=float)
        if x_eval_vec.size != n_features:
            raise ValueError(
                f"x_eval must have {n_features} entries to match design columns"
            )

        hazards = self._compute_hazards(beta_matrix, x_eval_vec)
        transition_matrix = self._compute_transition_matrix(hazards, z_eval)  # 推移確率行列 Pai

        log_likelihood = self._compute_log_likelihood(
            before, after, interval, design, beta_matrix
        )
        aic = -2.0 * log_likelihood + 2.0 * mask.sum()  # MATLAB の AIC 計算

        return EMarkovResult(
            beta_matrix=beta_matrix,
            t_values=t_values_matrix,
            hazards=hazards,
            transition_matrix=transition_matrix,
            log_likelihood=log_likelihood,
            aic=aic,
            iterations=iteration,
            error=errors[-1] if errors else np.inf,
            beta_flat=beta_flat,
            feature_scales=scales,
        )

    # ------------------------------------------------------------------
    # 内部ユーティリティ関数群
    # ------------------------------------------------------------------

    def _build_parameter_mask(self, n_params: int) -> np.ndarray:
        if self.parameter_mask is None:
            return np.ones(n_params, dtype=bool)
        mask = np.asarray(self.parameter_mask, dtype=bool)
        if mask.size != n_params:
            raise ValueError("parameter_mask length mismatch")
        return mask

    def _accumulate_sample_terms(
        self,
        grad: np.ndarray,
        hess: np.ndarray,
        before: int,
        after: int,
        interval: float,
        design_col: np.ndarray,
        beta_flat: np.ndarray,
        jmax: int,
        n_features: int,
    ) -> None:
        # 段階コードを内部では 0 始まりのインデックスに変換
        i = int(before) - 1
        j = int(after) - 1
        x = design_col

        beta = beta_flat.reshape((jmax - 1), n_features)
        theta = np.zeros(jmax, dtype=float)  # MATLAB の Theta 配列を Python で再現
        for l in range(jmax - 1):
            theta[l] = np.exp(beta[l] @ x)

        theta[:-1] = np.maximum(theta[:-1], 1e-12)

        thetasa = np.ones((jmax, jmax), dtype=float)  # Theta 差分行列
        for s in range(i, j + 1):
            for q in range(i, j + 1):
                if s != q:
                    diff = theta[s] - theta[q]
                    if abs(diff) < 1e-12:
                        diff = 1e-12 if s < q else -1e-12
                    thetasa[s, q] = diff

        df = np.zeros(jmax - 1, dtype=float)
        for l in range(i, j + 1):
            if l >= jmax - 1:
                continue
            sum2 = 0.0
            for h in range(i, j + 1):
                reserve = self._reserve_term(theta[h], interval, thetasa[:, h])
                if h == l:
                    sum1 = -interval
                    for p in range(i, j + 1):
                        if p != l:
                            sum1 += 1.0 / thetasa[p, l]
                else:
                    sum1 = -1.0 / thetasa[l, h]
                if l != j:
                    sum1 += 1.0 / theta[l]
                sum1 *= reserve
                sum2 += reserve
                df[l] += sum1
            df[l] /= max(sum2, 1e-12)

        hes = np.zeros((jmax - 1, jmax - 1), dtype=float)
        for l in range(i, j):
            if l >= jmax - 1:
                continue
            for n in range(l + 1, j + 1):
                if n >= jmax - 1:
                    continue
                sum2 = 0.0
                acc = 0.0
                for h in range(i, j + 1):
                    reserve = self._reserve_term(theta[h], interval, thetasa[:, h])
                    if h == l:
                        tmp = -interval
                        for p in range(i, j + 1):
                            if p != l:
                                tmp += 1.0 / thetasa[p, l]
                        tmp += 1.0 / theta[l] + 1.0 / thetasa[n, l]
                        sum1 = -tmp / thetasa[n, l]
                    elif h == n:
                        tmp = -interval
                        for p in range(i, j + 1):
                            if p != n:
                                tmp += 1.0 / thetasa[p, n]
                        tmp = tmp * ((1.0 / theta[l]) - (1.0 / thetasa[l, n]))
                        tmp -= 1.0 / (thetasa[l, n] ** 2)
                        sum1 = tmp
                    else:
                        tmp = (1.0 / theta[l]) - (1.0 / thetasa[l, h])
                        sum1 = -tmp / thetasa[n, h]
                    acc += sum1 * reserve
                    sum2 += reserve
                hes[l, n] = -df[l] * df[n] + acc / max(sum2, 1e-12)
                if n != j:
                    hes[l, n] += df[l] / theta[n]
                hes[n, l] = hes[l, n]

        for l in range(i, j + 1):
            if l >= jmax - 1:
                continue
            sum2 = 0.0
            acc = 0.0
            for h in range(i, j + 1):
                reserve = self._reserve_term(theta[h], interval, thetasa[:, h])
                tmp = 0.0
                for p in range(i, j + 1):
                    if p != l:
                        tmp += 1.0 / (thetasa[p, l] ** 2)
                if h == l:
                    res = -interval
                    for p in range(i, j + 1):
                        if p != l:
                            res += 1.0 / thetasa[p, l]
                    tmp += res ** 2
                    if l != j:
                        tmp += (res - (1.0 / theta[l])) / theta[l]
                else:
                    tmp = 2.0 / (thetasa[l, h] ** 2)
                    if l != j:
                        tmp -= (1.0 / theta[l]) ** 2
                        tmp -= 1.0 / (theta[l] * thetasa[l, h])
                acc += tmp * reserve
                sum2 += reserve
            value = -df[l] ** 2 + acc / max(sum2, 1e-12)
            if l != j:
                value += df[l] / theta[l]
            hes[l, l] = value

        # 勾配とヘッセ行列をフラットな配列に格納（MATLAB と同じ並び順）
        for l in range(jmax - 1):
            if l < i or l > j:
                continue
            xl = x
            for m in range(n_features):
                idx_lm = l * n_features + m
                grad[idx_lm] += df[l] * xl[m] * theta[l]
                for n in range(jmax - 1):
                    if n < i or n > j:
                        continue
                    xn = x
                    for m2 in range(n_features):
                        idx_nm2 = n * n_features + m2
                        hess[idx_lm, idx_nm2] += (
                            hes[l, n] * xl[m] * xn[m2] * theta[l] * theta[n]
                        )

    @staticmethod
    def _reserve_term(theta_val: float, interval: float, thetasa_col: np.ndarray) -> float:
        prod_val = np.prod(thetasa_col)  # MATLAB RESERVE の分母 prod(Thetasa(:,h))
        if prod_val == 0:
            prod_val = 1e-12
        exponent = -theta_val * interval
        exponent = np.clip(exponent, -700.0, 700.0)
        return float(np.exp(exponent) / prod_val)

    @staticmethod
    def _compute_hazards(beta_matrix: np.ndarray, x_eval: np.ndarray) -> np.ndarray:
        hazards = np.zeros(beta_matrix.shape[0] + 1, dtype=float)
        for idx, row in enumerate(beta_matrix):
            hazards[idx] = max(np.exp(row @ x_eval), 1e-12)
        return hazards

    def _compute_transition_matrix(self, hazards: np.ndarray, z_eval: float) -> np.ndarray:
        jmax = hazards.size
        transition = np.zeros((jmax, jmax), dtype=float)
        for i in range(jmax - 1):
            transition[i, i] = np.exp(-hazards[i] * z_eval)
            for j in range(i + 1, jmax - 1):
                transition[i, j] = self._transition_probability(hazards, i, j, z_eval)
        transition[:, -1] = 1.0 - transition[:, :-1].sum(axis=1)
        transition[-1, -1] = 1.0
        transition = np.clip(transition, 0.0, 1.0)
        row_sums = transition.sum(axis=1, keepdims=True)
        # 正常化して各行の合計を 1 に整える（数値誤差対策）
        for idx in range(jmax - 1):
            if row_sums[idx, 0] <= 0:
                transition[idx, :] = 0.0
                transition[idx, -1] = 1.0
            else:
                transition[idx, :] /= row_sums[idx, 0]
        return transition

    def _transition_probability(
        self, hazards: np.ndarray, i: int, j: int, z_eval: float
    ) -> float:
        if j == i:
            return float(np.exp(-hazards[i] * z_eval))
        if j == i + 1:
            hi, hj = hazards[i], hazards[j]
            if hi == hj:
                return float(hazards[i] * z_eval * np.exp(-hi * z_eval))
            return float((hi / (hi - hj)) * (-np.exp(-hi * z_eval) + np.exp(-hj * z_eval)))
        pr = np.prod(hazards[i:j])
        vals = []
        for k in range(i, j + 1):
            denom = 1.0
            for m in range(i, j + 1):
                if m == k:
                    continue
                diff = hazards[m] - hazards[k]
                if abs(diff) < 1e-12:
                    diff = 1e-12 if diff == 0 else np.sign(diff) * 1e-12
                denom *= diff
            vals.append((pr / denom) * np.exp(-hazards[k] * z_eval))
        return float(np.sum(vals))

    def _compute_log_likelihood(
        self,
        before: np.ndarray,
        after: np.ndarray,
        interval: np.ndarray,
        design: np.ndarray,
        beta_matrix: np.ndarray,
    ) -> float:
        log_likelihood = 0.0
        jmax = beta_matrix.shape[0] + 1
        for k in range(before.size):
            # ハザード計算（オーバーフロー防止）
            hazards = np.zeros(jmax, dtype=float)
            for idx in range(jmax - 1):
                z = float(beta_matrix[idx] @ design[:, k])
                z = np.clip(z, -700.0, 700.0)  # exp の安全域にクリップ
                hazards[idx] = max(np.exp(z), 1e-12)  # log(0) を避ける下駄

            i = int(before[k]) - 1
            j = int(after[k]) - 1
            z_eval = float(interval[k])

            if after[k] == jmax:
                # 吸収段に行ったケースは行全体を作って取り出す
                transition = self._compute_transition_matrix(hazards, z_eval)
                probability = transition[i, j]
            else:
                # 直接 i→j の成分だけ計算
                probability = self._transition_probability(hazards, i, j, z_eval)

            # 数値誤差で 1 を超えた場合は丸め、下限は ll_epsilon
            if probability > 1.0:
                probability = 1.0
            probability = max(probability, self.ll_epsilon)
            log_likelihood += np.log(probability)
        return log_likelihood


# ----------------------------------------------------------------------
# データ前処理用の補助関数
# ----------------------------------------------------------------------

def prepare_transition_arrays(
    frame: "pd.DataFrame",
    before_value: int = 1,
    after_col: str = "tenken.kiroku.hantei_kubun",
    nendo_col: str = "tenken.nendo",
    reference_col: str = "syogen.kyouyou_nendo",
    dropna: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """DataFrame から before/after/interval 配列を構成する。

    Parameters
    ----------
    before_value : int
        点検前の段階を表す定数。NationalRoadDB.txt と同様に既定値は 1。
    after_col : str
        点検後の段階を表す列名。
    nendo_col, reference_col : str
        点検年度と供用開始年度の列名。interval は nendo_col - reference_col で計算する。

    Returns
    -------
    before, after, interval : numpy arrays
        MATLAB の Be/Af/Ins に対応する配列。interval は正の値のみ残す。
    """

    if pd is None:
        raise ImportError("pandas is required to use prepare_transition_arrays")

    data = frame[[after_col, nendo_col, reference_col]].copy()  # MATLAB DB -> After/Interval に対応
    data["before"] = before_value
    data["interval"] = data[nendo_col] - data[reference_col]

    if dropna:
        data = data.dropna(subset=[after_col, "interval"])

    data = data[data["interval"] > 0]

    before = data["before"].astype(int).to_numpy()
    after = data[after_col].astype(int).to_numpy()
    interval = data["interval"].astype(float).to_numpy()
    return before, after, interval


def build_design_matrix(
    n_samples: int,
    feature_values: Optional[Iterable[Sequence[float]]] = None,
    include_intercept: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """推定に用いる設計行列を作成する。

    Parameters
    ----------
    n_samples : int
        サンプル数。切片列の長さに使用する。
    feature_values : iterable of sequences, optional
        各列の値を含むイテラブル。長さは ``n_samples`` で、順に列へ追加される。
        ``None`` の場合は切片のみとなる。
    include_intercept : bool, default True
        切片列（全て 1）を追加するかどうか。

    Returns
    -------
    matrix : ndarray (n_samples, n_features)
    scales : ndarray
        内部正規化で使用した列ごとのスケール。
    """

    columns = []
    scales = []
    if include_intercept:
        columns.append(np.ones(n_samples, dtype=float))
    if feature_values is not None:
        for values in feature_values:
            col = np.asarray(values, dtype=float)
            if col.shape != (n_samples,):
                raise ValueError("feature column length mismatch")
            columns.append(col)
    if not columns:
        raise ValueError("Design matrix requires at least one column (e.g., intercept)")
    matrix = np.column_stack(columns)  # MATLAB rXk → Xk を Python の形に構成
    # 内部正規化前のスケールを保持しておく（後段の確認用）
    for idx in range(matrix.shape[1]):
        val = np.nanmax(np.abs(matrix[:, idx]))
        if not np.isfinite(val) or val == 0:
            val = 1.0
        scales.append(val)
    return matrix, np.asarray(scales)


def load_legacy_transition_data(
    path: str,
    n_stages: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """NationalRoadDB.txt 形式を pandas で柔軟に読み込む（ヘッダ/区切り/ローマ数字に対応）。"""

    if pd is None:
        raise ImportError("pandas is required to load legacy transition data")

    import pandas as _pd

    # 1) 区切り文字はタブ優先で自動判定
    try:
        df = _pd.read_csv(path, sep="\t")
    except Exception:
        df = _pd.read_csv(path)

    colmap = {c.lower(): c for c in df.columns}
    for need in ("before", "after", "interval"):
        if need not in colmap:
            raise ValueError(f"required column '{need}' not found in file header: {df.columns.tolist()}")

    c_before = colmap["before"]
    c_after = colmap["after"]
    c_interval = colmap["interval"]

    def _roman_to_int_series(series: _pd.Series) -> _pd.Series:
        romans = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        s = series.astype(str)
        uniq = sorted(set(s.dropna()))
        if uniq and all(u in romans for u in uniq):
            order = [u for u in romans if u in uniq]
            mapping = {u: i + 1 for i, u in enumerate(order)}
            return s.map(mapping).astype(int)
        vals = _pd.to_numeric(series, errors="coerce")
        return vals.fillna(0).astype(int)

    before = _roman_to_int_series(df[c_before]).to_numpy(dtype=int)
    after = _roman_to_int_series(df[c_after]).to_numpy(dtype=int)
    interval = _pd.to_numeric(df[c_interval], errors="coerce").to_numpy(dtype=float)

    # 任意で段階数をクリップ（吸収状態を上限で固定したいときに使う）
    def _clip_optional(arr: np.ndarray, upper: Optional[int]) -> np.ndarray:
        if upper is None:
            return arr
        return np.clip(arr, 1, upper)

    # 補助変数（例：var4）があれば1列追加、それ以外は切片のみ
    feature_values: Optional[Iterable[Sequence[float]]] = None
    if "var4" in df.columns:
        feature_values = [np.asarray(df["var4"], dtype=float)]

    design_matrix, scales = build_design_matrix(
        n_samples=len(df),
        feature_values=feature_values,
        include_intercept=True,
    )
    return _clip_optional(before, n_stages), _clip_optional(after, n_stages), interval, design_matrix, scales


# ==== MATLAB 互換：XB・DE から parameter_mask を作るユーティリティ ====
def build_mask_from_matlab_XB(
    XB: np.ndarray,
    jmax: int,
    n_features: int,
    DE: Optional[Sequence[Tuple[int, int]]] = None,
) -> np.ndarray:
    """
    MATLAB の XB（長さ = (jmax-1)*n_features）と DE（(変数, 段階)の1始まり）から
    parameter_mask（True=推定，False=固定0）を構築する。
    """
    XB = np.asarray(XB, dtype=float).reshape(-1)
    if XB.size != (jmax - 1) * n_features:
        raise ValueError("XB length mismatch for given jmax and n_features")

    mask = XB != 0.0  # MATLAB の XP=find(XB~=0) に相当
    if DE:
        for M, l in DE:
            if (1 <= M <= n_features) and (1 <= l <= jmax - 1):
                idx = (l - 1) * n_features + (M - 1)
                mask[idx] = False
    return mask


# ==== MATLAB 互換：XBP（評価用説明変数）を設計行列次元に合わせて作る ====
def build_x_eval_from_XBP(XBP: Sequence[float], n_features: int) -> np.ndarray:
    x_eval = np.asarray(XBP, dtype=float).reshape(-1)
    if x_eval.size != n_features:
        raise ValueError(f"XBP length must equal n_features={n_features}, got {x_eval.size}")
    return x_eval


def coerce_XB_length(
    XB: Sequence[float],
    jmax: int,
    n_features: int,
    pad_value: float = 0.0,
) -> np.ndarray:
    """
    MATLAB 由来の XB を期待サイズ (jmax-1)*n_features に整形する。
    短ければ埋め、長ければ切り詰める。
    """
    XB = np.asarray(XB, dtype=float).reshape(-1)
    expected = (jmax - 1) * n_features
    if XB.size == expected:
        return XB
    if XB.size == n_features:
        return np.tile(XB, (jmax - 1))  # 特徴ブロックを段階方向にタイル
    if XB.size == (jmax - 1):
        return np.repeat(XB, n_features)  # 段階ブロックを特徴方向にリピート
    if XB.size < expected:
        return np.pad(XB, (0, expected - XB.size), constant_values=pad_value)
    return XB[:expected]


def save_emarkov_result(
    result: EMarkovResult,
    out_dir: str,
    prefix: str = "emarkov",
) -> None:
    """
    EMarkovResult を人が読みやすい形式で保存するヘルパー。

    - ハザード、遷移行列、係数、t値を CSV で保存
    - LL/AIC/反復回数/誤差などを JSON で保存
    - 保存先ディレクトリは呼び出し側（例: 20251206.ipynb の output_dir）で用意しておく
    """

    if not os.path.isdir(out_dir):
        raise FileNotFoundError(f"out_dir not found: {out_dir}")

    np.savetxt(
        os.path.join(out_dir, f"{prefix}_hazards.csv"),
        np.atleast_2d(result.hazards),
        delimiter=",",
    )
    np.savetxt(
        os.path.join(out_dir, f"{prefix}_transition_matrix.csv"),
        result.transition_matrix,
        delimiter=",",
    )
    np.savetxt(
        os.path.join(out_dir, f"{prefix}_beta_matrix.csv"),
        result.beta_matrix,
        delimiter=",",
    )
    np.savetxt(
        os.path.join(out_dir, f"{prefix}_t_values.csv"),
        result.t_values,
        delimiter=",",
    )
    np.savetxt(
        os.path.join(out_dir, f"{prefix}_feature_scales.csv"),
        np.atleast_2d(result.feature_scales),
        delimiter=",",
    )

    metrics = {
        "log_likelihood": float(result.log_likelihood),
        "aic": float(result.aic),
        "iterations": int(result.iterations),
        "error": float(result.error),
    }
    with open(os.path.join(out_dir, f"{prefix}_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

def demo_with_national_roads(
    path: str = "NationalRoadDB.txt",
    estimator: Optional[EMarkovEstimator] = None,
    XB: Optional[Sequence[float]] = None,
    DE: Optional[Sequence[Tuple[int, int]]] = None,
    XBP: Optional[Sequence[float]] = None,
    ZP: float = 1.0,
    n_stages: Optional[int] = 4,
) -> EMarkovResult:
    """MATLAB スクリプトと同じ流儀で NationalRoadDB.txt を推定するラッパー。"""

    before, after, interval, design_matrix, _ = load_legacy_transition_data(
        path, n_stages=n_stages
    )
    jmax = int(after.max())
    n_features = design_matrix.shape[1]

    if estimator is None:
        estimator = EMarkovEstimator(
            matlab_convergence=True,
            scaling_method="max",
            final_iter_no_ridge=3,
            ridge_lambda=1e-8,
            verbose=True,
            ll_epsilon=1e-300,
        )

    # MATLAB の XB/DE をそのまま渡せるように整形
    if XB is None:
        # 段階ごとに強めの負の切片を入れておく（初期値起因の発散を抑制）
        XB = np.zeros((jmax - 1) * n_features, dtype=float)
        for l in range(1, jmax):
            XB[(l - 1) * n_features + 0] = -2.0 * l
    else:
        XB = np.asarray(XB, dtype=float).reshape(-1)

    XB = coerce_XB_length(XB, jmax=jmax, n_features=n_features, pad_value=0.0)
    mask = build_mask_from_matlab_XB(XB, jmax=jmax, n_features=n_features, DE=DE)
    initial_beta = XB.copy()

    # 推移確率の評価点（デフォルトは全て1）
    if XBP is None:
        x_eval = np.ones(n_features, dtype=float)
    else:
        x_eval = build_x_eval_from_XBP(XBP, n_features=n_features)
    z_eval = float(ZP)

    estimator.parameter_mask = mask
    return estimator.fit(
        before,
        after,
        interval,
        design_matrix,
        initial_beta=initial_beta,
        x_eval=x_eval,
        z_eval=z_eval,
    )


__all__ = [
    "EMarkovEstimator",
    "EMarkovResult",
    "prepare_transition_arrays",
    "build_design_matrix",
    "load_legacy_transition_data",
    "build_mask_from_matlab_XB",
    "build_x_eval_from_XBP",
    "coerce_XB_length",
    "save_emarkov_result",
    "demo_with_national_roads",
]


if __name__ == "__main__":
    # python -m bundling_analysis.emarkov_estimator を実行した際の出力。
    # MATLAB eMarkov.m と同じ指標を並べて表示する。
    result = demo_with_national_roads()
    print("=== eMarkov Python Demo (NationalRoadDB.txt) ===")
    print(f"Iterations: {result.iterations}")
    print(f"Convergence error: {result.error:.3e}")
    print("Beta matrix (stage x variables):")
    print(result.beta_matrix)
    print("t-values (stage x variables):")
    print(result.t_values)
    print("Hazards:")
    print(result.hazards)
    print("Transition matrix:")
    print(result.transition_matrix)
    print(f"Log-likelihood: {result.log_likelihood:.6f}")
    print(f"AIC: {result.aic:.6f}")
