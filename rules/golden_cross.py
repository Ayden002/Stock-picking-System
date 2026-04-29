"""
金叉规则 - 检查周线（或日线）真金叉

改进点：
  1. 只使用已收盘的完整周线（丢掉最后一根未走完的周线）
  2. 真金叉判定：上一周 MA_short ≤ MA_long，本周 MA_short > MA_long
  3. 均线方向过滤：要求 MA_long 本周 ≥ 上周（趋势向上）
  4. 可配置最大回溯周数，在最近 N 周内发生过金叉即视为通过
"""
import pandas as pd
from datetime import datetime
from rules.base import BaseRule


class GoldenCrossRule(BaseRule):
    """周线/日线均线真金叉规则

    Args:
        ma_short (int): 短期均线周期，默认 5
        ma_long  (int): 长期均线周期，默认 10
        use_weekly (bool): True=使用周线，False=使用日线，默认 True
        lookback_weeks (int): 在最近 N 根K线内发生过金叉即通过，默认 2
        require_ma_long_up (bool): 是否要求长期均线方向向上，默认 True
    """

    name = "均线金叉"

    def __init__(self, ma_short: int = 5, ma_long: int = 10,
                 use_weekly: bool = True, lookback_weeks: int = 2,
                 require_ma_long_up: bool = True):
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.use_weekly = use_weekly
        self.lookback_weeks = lookback_weeks
        self.require_ma_long_up = require_ma_long_up

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None) -> dict:
        df = weekly_df if (self.use_weekly and weekly_df is not None) else daily_df

        min_len = self.ma_long + self.lookback_weeks + 1
        if df is None or len(df) < min_len:
            return {"passed": False, "detail": {"reason": f"数据不足（需要 {min_len} 条）"}}

        # 如果是周线且当前周尚未走完，丢掉最后一根不完整的周线
        if self.use_weekly and weekly_df is not None:
            df = self._drop_incomplete_week(df)
            if len(df) < min_len:
                return {"passed": False, "detail": {"reason": "去掉未完成周后数据不足"}}

        ma_s = df["收盘价"].rolling(self.ma_short).mean()
        ma_l = df["收盘价"].rolling(self.ma_long).mean()

        # 在最近 lookback_weeks 根K线内寻找真金叉
        golden_cross_found = False
        cross_bar_idx = -1
        for i in range(1, self.lookback_weeks + 1):
            idx = len(df) - i
            prev_idx = idx - 1
            if prev_idx < 0:
                continue
            cur_s, cur_l = ma_s.iloc[idx], ma_l.iloc[idx]
            pre_s, pre_l = ma_s.iloc[prev_idx], ma_l.iloc[prev_idx]
            if pd.isna(cur_s) or pd.isna(cur_l) or pd.isna(pre_s) or pd.isna(pre_l):
                continue
            # 真金叉: 前一根 MA_short ≤ MA_long，当前 MA_short > MA_long
            if pre_s <= pre_l and cur_s > cur_l:
                # 均线方向过滤
                if self.require_ma_long_up and cur_l < pre_l:
                    continue
                golden_cross_found = True
                cross_bar_idx = idx
                break

        latest_s = float(ma_s.iloc[-1])
        latest_l = float(ma_l.iloc[-1])

        return {
            "passed": golden_cross_found,
            "detail": {
                f"ma{self.ma_short}": round(latest_s, 4),
                f"ma{self.ma_long}": round(latest_l, 4),
                "use_weekly": self.use_weekly,
                "cross_type": "真金叉" if golden_cross_found else "无",
                "cross_bar_date": str(df["日期"].iloc[cross_bar_idx])[:10] if golden_cross_found else None,
            },
        }

    @staticmethod
    def _drop_incomplete_week(df: pd.DataFrame) -> pd.DataFrame:
        """如果最后一根周线所在的周尚未结束（今天不是周日），就丢掉它""" 
        if df.empty:
            return df
        today = datetime.now()
        # weekday(): Monday=0 ... Sunday=6
        # 如果今天还没到周日，说明本周未收完
        if today.weekday() < 6:
            last_date = pd.Timestamp(df["日期"].iloc[-1])
            # 最后一条数据在本周内，则丢掉
            if last_date.isocalendar()[1] == today.isocalendar()[1] and last_date.year == today.year:
                return df.iloc[:-1]
        return df
 