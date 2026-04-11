"""
组合管理与风控模块

提供基础组合管理能力：
  - 最大持仓数限制
  - 等权仓位分配
  - 简单止损止盈检查
"""

from portfolio.manager import PortfolioManager

__all__ = ["PortfolioManager"]
