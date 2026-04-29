"""
箱体突破规则 (BoxBreakoutRule)
==============================

判定逻辑：
  当日（或最近 N 日内）收盘价 > 前 box_window 个交易日最高价 * (1 + min_break_pct)
  且 当日成交量 / 前 box_window 日均量 >= vol_ratio

用于捕捉真突破（如 603788 4/21 突破 30 日箱顶 15.88 + 放量 7×）。
"""
from __future__ import annotations

import pandas as pd

from rules.base import BaseRule


class BoxBreakoutRule(BaseRule):
    """箱体突破规则

    Args:
        box_window (int):     箱体观察窗口，默认 30
        lookback_days (int):  在最近 N 日内出现过突破即通过，默认 3
        min_break_pct (float): 突破阈值百分比，默认 0.005（0.5%）
        vol_ratio (float):    放量倍数（突破日 vs 箱体均量），默认 1.5
    """

    name = "箱体突破"

    def __init__(
        self,
        box_window: int = 30,
        lookback_days: int = 3,
        min_break_pct: float = 0.005,
        vol_ratio: float = 1.5,
    ):
        self.box_window = box_window
        self.lookback_days = lookback_days
        self.min_break_pct = min_break_pct
        self.vol_ratio = vol_ratio

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None, **kwargs) -> dict:
        need = self.box_window + self.lookback_days + 1
        if daily_df is None or len(daily_df) < need:
            return {"passed": False, "detail": {"reason": f"数据不足（需要 {need} 条）"}}

        df = daily_df.reset_index(drop=True)

        breakout_date = None
        break_pct = None
        vmul = None

        # 在最近 lookback_days 内找一次有效突破
        for i in range(self.lookback_days):
            idx = len(df) - 1 - i
            box = df.iloc[idx - self.box_window : idx]
            if len(box) < self.box_window:
                continue
            box_high = float(box["最高价"].max())
            box_avg_vol = float(box["成交量"].mean())
            if box_high <= 0 or box_avg_vol <= 0:
                continue
            today = df.iloc[idx]
            cur_close = float(today["收盘价"])
            cur_vol = float(today["成交量"])

            pct = (cur_close - box_high) / box_high
            multiple = cur_vol / box_avg_vol
            if pct >= self.min_break_pct and multiple >= self.vol_ratio:
                breakout_date = today["日期"]
                break_pct = pct
                vmul = multiple
                break

        passed = breakout_date is not None

        bd_str = (
            breakout_date.strftime("%Y-%m-%d")
            if breakout_date is not None and hasattr(breakout_date, "strftime")
            else (str(breakout_date)[:10] if breakout_date is not None else None)
        )
        return {
            "passed": passed,
            "detail": {
                "breakout_date": bd_str,
                "break_pct": round(break_pct, 4) if break_pct is not None else None,
                "vol_multiple": round(vmul, 2) if vmul is not None else None,
                "box_window": self.box_window,
            },
        }
