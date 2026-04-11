"""
涨停规则 - 检查最近 N 个交易日是否有涨停（单日涨幅≥阈值）
"""
import pandas as pd
from rules.base import BaseRule


class LimitUpRule(BaseRule):
    """涨停规则

    Args:
        days (int): 向前检查的交易日数，默认 15
        threshold (float): 涨停判定阈值（涨幅），默认 0.095（即 9.5%）
    """

    name = "涨停检测"

    def __init__(self, days: int = 15, threshold: float = 0.095):
        self.days = days
        self.threshold = threshold

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None) -> dict:
        if daily_df is None or len(daily_df) < 2:
            return {"passed": False, "detail": {"reason": "数据不足"}}

        recent = daily_df.tail(self.days).copy()
        recent["日收益率"] = recent["收盘价"].pct_change()

        hits = recent[recent["日收益率"] >= self.threshold]
        passed = len(hits) > 0

        limit_up_dates = [
            d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            for d in hits["日期"].tolist()
        ]
        max_increase = float(recent["日收益率"].max()) if not recent["日收益率"].isna().all() else 0.0

        return {
            "passed": passed,
            "detail": {
                "limit_up_dates": limit_up_dates,
                "max_increase": round(max_increase, 6),
                "check_days": self.days,
                "threshold": self.threshold,
            },
        }
