"""
组合管理器 - 仓位分配与风控

用法示例：
    from portfolio import PortfolioManager

    pm = PortfolioManager(max_positions=10, total_capital=100000)
    allocation = pm.allocate(passed_stocks)
    pm.print_allocation(allocation)
"""
from __future__ import annotations

from logger import get_logger

logger = get_logger(__name__)


class PortfolioManager:
    """基础组合管理器

    Args:
        max_positions (int): 最大持仓数量，默认 10
        total_capital (float): 总资金（元），默认 100_000
        stop_loss (float): 止损线（跌幅），默认 0.05（即 -5%）
        take_profit (float): 止盈线（涨幅），默认 0.10（即 +10%）
        min_position_pct (float): 单票最小仓位比例，默认 0.05
        max_position_pct (float): 单票最大仓位比例，默认 0.20
    """

    def __init__(
        self,
        max_positions: int = 10,
        total_capital: float = 100_000.0,
        stop_loss: float = 0.05,
        take_profit: float = 0.10,
        min_position_pct: float = 0.05,
        max_position_pct: float = 0.20,
    ):
        self.max_positions = max_positions
        self.total_capital = total_capital
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.min_position_pct = min_position_pct
        self.max_position_pct = max_position_pct

    # ------------------------------------------------------------------
    # 仓位分配
    # ------------------------------------------------------------------
    def allocate(self, stocks: list[dict]) -> list[dict]:
        """对选出的股票做等权分配，受最大持仓数限制。

        Args:
            stocks: 选股结果列表，每项至少包含 ``code`` 和 ``details.latest_close``。

        Returns:
            list[dict]: 每项追加了 ``weight``、``capital`` 和 ``shares`` 字段。
        """
        if not stocks:
            return []

        # 截取最多 max_positions 只
        candidates = stocks[: self.max_positions]
        n = len(candidates)

        # 等权
        weight = 1.0 / n
        # 约束在 [min_pct, max_pct] 范围内
        weight = max(self.min_position_pct, min(self.max_position_pct, weight))

        result = []
        for stock in candidates:
            capital = self.total_capital * weight
            try:
                price = float(stock["details"]["latest_close"])
                shares = int(capital / price / 100) * 100  # 按手取整
            except (KeyError, TypeError, ZeroDivisionError):
                price = 0.0
                shares = 0

            result.append(
                {
                    **stock,
                    "weight": round(weight, 4),
                    "capital": round(capital, 2),
                    "shares": shares,
                }
            )

        logger.info(
            f"仓位分配完成：{n} 只股票，单票权重 {weight:.2%}，"
            f"单票资金约 {self.total_capital * weight:,.0f} 元"
        )
        return result

    # ------------------------------------------------------------------
    # 止损止盈检查
    # ------------------------------------------------------------------
    def check_risk(self, code: str, cost_price: float, current_price: float) -> str:
        """检查持仓是否触发止损或止盈。

        Args:
            code: 股票代码
            cost_price: 成本价
            current_price: 当前价

        Returns:
            str: "stop_loss" / "take_profit" / "hold"
        """
        if cost_price <= 0:
            return "hold"
        change = (current_price - cost_price) / cost_price
        if change <= -self.stop_loss:
            logger.info(f"{code} 触发止损：{change:.2%}（阈值 -{self.stop_loss:.2%}）")
            return "stop_loss"
        if change >= self.take_profit:
            logger.info(f"{code} 触发止盈：{change:.2%}（阈值 +{self.take_profit:.2%}）")
            return "take_profit"
        return "hold"

    # ------------------------------------------------------------------
    # 打印分配表
    # ------------------------------------------------------------------
    @staticmethod
    def print_allocation(allocation: list[dict]) -> None:
        if not allocation:
            print("没有可分配的股票。")
            return
        print("\n" + "=" * 65)
        print("组合分配方案")
        print("=" * 65)
        print(f"{'代码':<8} {'最新价':>8} {'权重':>7} {'分配资金':>12} {'参考股数':>9}")
        print("-" * 65)
        for item in allocation:
            code = item.get("code", "-")
            price = item.get("details", {}).get("latest_close", 0)
            weight = item.get("weight", 0)
            capital = item.get("capital", 0)
            shares = item.get("shares", 0)
            print(
                f"{code:<8} {price:>8.2f} {weight:>6.2%} {capital:>12,.0f} {shares:>9,}"
            )
        print("=" * 65 + "\n")
