"""
波动率收敛 (VCP, Volatility Contraction Pattern) 规则
=====================================================

核心思想（Mark Minervini）：
  突破前股价波动会持续收窄，形成"价格收口"（Coiled Spring）。
  公式：std(close, short_n) / std(close, long_n)  < threshold

附带要求：
  * 价格在 long_n 内不大幅下跌（避免下跌途中的"假收敛"）
  * 当前 close 不能距离 short_n 高点过远（避免已经突破再追）

判定 603788 4/13-4/20 那一周可被识别（long=30/short=10 比值 ≈ 0.55）。
"""
from __future__ import annotations

import pandas as pd

from rules.base import BaseRule


class VCPRule(BaseRule):
    """波动率收敛规则

    Args:
        short_n (int):   短期窗口，默认 10
        long_n (int):    长期窗口，默认 30
        threshold (float): std 比值阈值，< 此值即触发，默认 0.6
        max_drawdown_in_long (float): long_n 内最大跌幅上限（避免下跌中），默认 0.2
        max_dist_to_high (float): 当前价距 short_n 最高价比例上限，默认 0.05
                                   （即只在贴近箱顶时才触发，避免追高）
    """

    name = "波动收敛VCP"

    def __init__(
        self,
        short_n: int = 10,
        long_n: int = 30,
        threshold: float = 0.6,
        max_drawdown_in_long: float = 0.2,
        max_dist_to_high: float = 0.05,
    ):
        self.short_n = short_n
        self.long_n = long_n
        self.threshold = threshold
        self.max_drawdown_in_long = max_drawdown_in_long
        self.max_dist_to_high = max_dist_to_high

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None, **kwargs) -> dict:
        if daily_df is None or len(daily_df) < self.long_n + 2:
            return {"passed": False, "detail": {"reason": "数据不足"}}

        df = daily_df.tail(self.long_n + 1).reset_index(drop=True)
        close = df["收盘价"]

        std_short = float(close.tail(self.short_n).std(ddof=0))
        std_long = float(close.std(ddof=0))
        if std_long <= 0:
            return {"passed": False, "detail": {"reason": "长期波动为 0"}}

        ratio = std_short / std_long

        # 长期窗口内最大跌幅
        dd = float(1 - close.min() / close.max())

        # 当前价距 short_n 最高价
        recent_high = float(close.tail(self.short_n).max())
        cur = float(close.iloc[-1])
        dist_to_high = (recent_high - cur) / recent_high if recent_high > 0 else 1.0

        passed = (
            ratio <= self.threshold
            and dd <= self.max_drawdown_in_long
            and dist_to_high <= self.max_dist_to_high
        )

        return {
            "passed": passed,
            "detail": {
                "std_ratio": round(ratio, 4),
                "drawdown_in_long": round(dd, 4),
                "dist_to_high_pct": round(dist_to_high, 4),
                "short_n": self.short_n,
                "long_n": self.long_n,
            },
        }
