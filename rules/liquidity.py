"""
流动性 / 噪音剔除规则 (LiquidityRule)
=====================================

剔除以下垃圾标的：
  * 20 日平均成交额 < min_amount_wan（默认 5000 万）
  * 20 日平均换手率 < min_turnover_pct（默认 0.5%）

注意：本规则属于 Layer-1 前置过滤，不参与综合评分；
      不通过即视为整只股票出局（在 stock_selector 中通过 VETO 实现）。
"""
from __future__ import annotations

import pandas as pd

from rules.base import BaseRule


class LiquidityRule(BaseRule):
    """流动性过滤

    Args:
        avg_period (int):       平均窗口，默认 20
        min_amount_wan (float): 最小日均成交额（万元），默认 5000
        min_turnover_pct (float|None): 最小日均换手率（百分比，如 0.5），None=不检查
    """

    name = "流动性过滤"

    def __init__(
        self,
        avg_period: int = 20,
        min_amount_wan: float = 5000.0,
        min_turnover_pct: float | None = 0.5,
    ):
        self.avg_period = avg_period
        self.min_amount_wan = min_amount_wan
        self.min_turnover_pct = min_turnover_pct

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None, **kwargs) -> dict:
        if daily_df is None or len(daily_df) < self.avg_period:
            return {"passed": False, "detail": {"reason": "数据不足"}}

        recent = daily_df.tail(self.avg_period)

        # 成交额：tushare pro.daily 返回 amount 单位为"千元"
        # 千元 -> 万元 即 / 10
        amt_col = recent.get("成交额")
        if amt_col is None:
            return {"passed": False, "detail": {"reason": "缺少成交额列"}}
        avg_amt_wan = float(amt_col.mean()) / 10.0  # 千元 -> 万元

        # 换手率（百分比，如 1.23 表示 1.23%）
        # 注意：tushare pro.daily 不返回换手率，缓存中该列恒为 0；
        # 若全部为 0 视为字段缺失，跳过换手率检查
        avg_turnover = None
        if "换手率" in recent.columns:
            tv = float(recent["换手率"].mean())
            if tv > 0:
                avg_turnover = tv

        veto = None
        if avg_amt_wan < self.min_amount_wan:
            veto = f"日均成交额 {avg_amt_wan:.0f} 万 < {self.min_amount_wan:.0f} 万"
        elif (
            self.min_turnover_pct is not None
            and avg_turnover is not None
            and avg_turnover < self.min_turnover_pct
        ):
            veto = f"日均换手率 {avg_turnover:.2f}% < {self.min_turnover_pct}%"

        return {
            "passed": veto is None,
            "detail": {
                "avg_amount_wan": round(avg_amt_wan, 1),
                "avg_turnover_pct": round(avg_turnover, 3) if avg_turnover is not None else None,
                "veto_reason": veto,
            },
        }
