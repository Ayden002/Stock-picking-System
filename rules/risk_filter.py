"""
超买/极端值风险过滤器 (RiskFilterRule)
======================================

设计目标：避免在 RSI 极度超买 / KDJ J 值穿顶 时入选（如 603788 4/21 RSI=82.6 J=101）。

包含三个子指标：
  B1. RSI(14)            ：>= rsi_overbought 一票否决
  B2. KDJ J 值           ：>= kdj_j_overbought 一票否决（默认 100）
  B3. Bollinger 位置     ：close 在布林带 +0.8σ 之上时扣分（不直接否决，作为风险标记）

通过条件：三项均不触发否决 → passed=True。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from rules.base import BaseRule


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _kdj(df: pd.DataFrame, n: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    low_n = df["最低价"].rolling(n).min()
    high_n = df["最高价"].rolling(n).max()
    rsv = (df["收盘价"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def _bollinger_position(close: pd.Series, n: int = 20) -> pd.Series:
    ma = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return (close - ma) / (2 * sd.replace(0, np.nan))


class RiskFilterRule(BaseRule):
    """超买防御过滤

    Args:
        rsi_period (int):           RSI 周期，默认 14
        rsi_overbought (float):     RSI 超买阈值，>= 即否决，默认 80
        kdj_n (int):                KDJ 周期，默认 9
        kdj_j_overbought (float):   J 值超买阈值，默认 100
        boll_warn_z (float):        布林位置警告阈值，默认 0.8（仅记录，不否决）
    """

    name = "风险过滤"

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_overbought: float = 80.0,
        kdj_n: int = 9,
        kdj_j_overbought: float = 100.0,
        boll_warn_z: float = 0.8,
    ):
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.kdj_n = kdj_n
        self.kdj_j_overbought = kdj_j_overbought
        self.boll_warn_z = boll_warn_z

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None, **kwargs) -> dict:
        if daily_df is None or len(daily_df) < max(self.rsi_period, self.kdj_n, 20) + 5:
            return {"passed": False, "detail": {"reason": "数据不足"}}

        df = daily_df.copy()

        rsi_series = _rsi(df["收盘价"], self.rsi_period)
        _, _, j_series = _kdj(df, self.kdj_n)
        boll_z = _bollinger_position(df["收盘价"], 20)

        rsi_v = float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else None
        j_v = float(j_series.iloc[-1]) if pd.notna(j_series.iloc[-1]) else None
        boll_v = float(boll_z.iloc[-1]) if pd.notna(boll_z.iloc[-1]) else None

        veto = None
        if rsi_v is not None and rsi_v >= self.rsi_overbought:
            veto = f"RSI {rsi_v:.1f} >= {self.rsi_overbought}（严重超买）"
        elif j_v is not None and j_v >= self.kdj_j_overbought:
            veto = f"KDJ J {j_v:.1f} >= {self.kdj_j_overbought}（极值穿顶）"

        warn = None
        if boll_v is not None and boll_v >= self.boll_warn_z:
            warn = f"布林位置 {boll_v:.2f} σ（贴上轨）"

        return {
            "passed": veto is None,
            "detail": {
                "rsi14": round(rsi_v, 2) if rsi_v is not None else None,
                "kdj_j": round(j_v, 2) if j_v is not None else None,
                "boll_z": round(boll_v, 3) if boll_v is not None else None,
                "veto_reason": veto,
                "warn": warn,
            },
        }
