"""
金叉规则 - 检查周线（或日线）MA5 > MA10
"""
import pandas as pd
from rules.base import BaseRule


class GoldenCrossRule(BaseRule):
    """周线/日线均线金叉规则

    默认使用周线数据判断 MA5 > MA10（即短期均线在长期均线上方）。
    可通过参数切换为日线，或修改均线周期。

    Args:
        ma_short (int): 短期均线周期，默认 5
        ma_long  (int): 长期均线周期，默认 10
        use_weekly (bool): True=使用周线，False=使用日线，默认 True
    """

    name = "均线金叉"

    def __init__(self, ma_short: int = 5, ma_long: int = 10, use_weekly: bool = True):
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.use_weekly = use_weekly

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None) -> dict:
        df = weekly_df if (self.use_weekly and weekly_df is not None) else daily_df

        min_len = self.ma_long + 1
        if df is None or len(df) < min_len:
            return {"passed": False, "detail": {"reason": f"数据不足（需要 {min_len} 条）"}}

        ma_s = df["收盘价"].rolling(self.ma_short).mean()
        ma_l = df["收盘价"].rolling(self.ma_long).mean()

        latest_s = float(ma_s.iloc[-1])
        latest_l = float(ma_l.iloc[-1])
        passed = latest_s > latest_l

        return {
            "passed": passed,
            "detail": {
                f"ma{self.ma_short}": round(latest_s, 4),
                f"ma{self.ma_long}": round(latest_l, 4),
                "use_weekly": self.use_weekly,
            },
        }
