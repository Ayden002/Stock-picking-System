"""
倍量规则 - 检查最近 N 个交易日是否有单日成交量超过前 M 日均量的 ratio 倍
"""
import pandas as pd
from rules.base import BaseRule


class VolumeSpikeRule(BaseRule):
    """倍量规则

    Args:
        days (int): 向前检查的交易日数，默认 5
        ratio (float): 倍量倍数，默认 2.0（即 2 倍均量）
        avg_period (int): 计算基准均量所用的回溯天数，默认 20
    """

    name = "倍量检测"

    def __init__(self, days: int = 5, ratio: float = 2.0, avg_period: int = 20):
        self.days = days
        self.ratio = ratio
        self.avg_period = avg_period

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None) -> dict:
        needed = self.avg_period + self.days
        if daily_df is None or len(daily_df) < needed:
            return {
                "passed": False,
                "detail": {"reason": f"数据不足（需要 {needed} 条，实际 {0 if daily_df is None else len(daily_df)} 条）"},
            }

        baseline = daily_df.iloc[-(self.avg_period + self.days) : -self.days]["成交量"]
        avg_vol = float(baseline.mean())

        if avg_vol == 0:
            return {"passed": False, "detail": {"reason": "基准均量为 0"}}

        recent = daily_df.tail(self.days).copy()
        recent["倍数"] = recent["成交量"] / avg_vol
        hits = recent[recent["倍数"] >= self.ratio]
        passed = len(hits) > 0

        volume_dates = [
            d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            for d in hits["日期"].tolist()
        ]
        max_multiple = float(recent["倍数"].max()) if not recent["倍数"].isna().all() else 0.0

        return {
            "passed": passed,
            "detail": {
                "volume_dates": volume_dates,
                "max_multiple": round(max_multiple, 4),
                "avg_volume": round(avg_vol, 2),
                "check_days": self.days,
                "ratio": self.ratio,
            },
        }
