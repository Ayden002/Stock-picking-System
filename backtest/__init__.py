"""
回测模块

提供最轻量可用的历史回测能力：
  - 给定选股结果（股票列表 + 选股日期），模拟 T+1 买入、持有 N 天后卖出
  - 统计收益率、胜率、平均收益、最大单次回撤
"""

from backtest.engine import BacktestEngine

__all__ = ["BacktestEngine"]
