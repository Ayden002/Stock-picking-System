"""
规则模块 - 可插拔的选股规则体系

每个规则都继承自 BaseRule，实现 evaluate() 方法。
可以自由组合多个规则，也可以快速新增自定义规则。

示例：
    from rules import GoldenCrossRule, LimitUpRule, VolumeSpikeRule
    rules = [GoldenCrossRule(), LimitUpRule(), VolumeSpikeRule()]
"""

from rules.base import BaseRule
from rules.golden_cross import GoldenCrossRule
from rules.limit_up import LimitUpRule
from rules.volume_spike import VolumeSpikeRule
from rules.main_flow import MainFlowRule
from rules.risk_filter import RiskFilterRule
from rules.vcp import VCPRule
from rules.box_breakout import BoxBreakoutRule
from rules.liquidity import LiquidityRule

__all__ = [
    "BaseRule",
    "GoldenCrossRule",
    "LimitUpRule",
    "VolumeSpikeRule",
    "MainFlowRule",
    "RiskFilterRule",
    "VCPRule",
    "BoxBreakoutRule",
    "LiquidityRule",
]
