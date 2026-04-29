"""
回测引擎

用法示例：
    from backtest import BacktestEngine
    from data_fetcher import DataFetcher

    fetcher = DataFetcher()
    engine = BacktestEngine(fetcher)

    # stocks: [{"code": "000001", "select_date": "2024-01-10"}, ...]
    report = engine.run(stocks, hold_days=5)
    engine.print_report(report)
"""
from __future__ import annotations

import pandas as pd
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger(__name__)


class BacktestEngine:
    """简单持有回测引擎

    Args:
        fetcher: DataFetcher 实例，用于获取历史行情
        hold_days (int): 默认持有天数，默认 5 个交易日
        commission (float): 单边手续费率，默认 0.0003（万三）
        slippage (float): 单边滑点（比例），默认 0.001
    """

    def __init__(self, fetcher, hold_days: int = 5,
                 commission: float = 0.0003, slippage: float = 0.001):
        self.fetcher = fetcher
        self.hold_days = hold_days
        self.commission = commission
        self.slippage = slippage
        self.logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(self, stocks: list[dict], hold_days: int | None = None) -> dict:
        """对选股结果做持有回测。

        Args:
            stocks: 每项包含 ``code`` 和 ``select_date``（字符串 YYYY-MM-DD 或 datetime）。
                    若没有 ``select_date``，则视为以最新可用收盘价买入（仅做参考）。
            hold_days: 持有交易日数，覆盖构造参数。

        Returns:
            dict: 回测汇总报告，包含 trades 列表与统计指标。
        """
        hold = hold_days if hold_days is not None else self.hold_days
        trades = []

        for item in stocks:
            code = item.get("code") or item.get("代码")
            select_date_raw = item.get("select_date") or item.get("选股日期")
            trade = self._simulate_trade(code, select_date_raw, hold)
            if trade:
                trades.append(trade)

        return self._summarize(trades)

    # ------------------------------------------------------------------
    # 单只股票模拟
    # ------------------------------------------------------------------
    def _simulate_trade(self, code: str, select_date_raw, hold_days: int) -> dict | None:
        """获取数据，找到买入价和卖出价，计算收益。"""
        try:
            # 拉取足够长的日线（选股日往前 30 天 + 持有天数 + 缓冲）
            df = self.fetcher.get_stock_daily(code, days=hold_days * 3 + 60)
            if df is None or df.empty:
                return None

            df = df.sort_values("日期").reset_index(drop=True)

            if select_date_raw:
                select_date = pd.to_datetime(select_date_raw)
            else:
                select_date = df["日期"].iloc[-1]

            # 找 T+1 买入日（选股日之后第一个交易日）
            after = df[df["日期"] > select_date]
            if after.empty:
                self.logger.debug(f"{code}: 没有选股日之后的数据，跳过")
                return None

            buy_idx = after.index[0]
            buy_row = df.loc[buy_idx]
            buy_price = float(buy_row["开盘价"]) * (1 + self.slippage)

            # 找卖出日（买入后第 hold_days 个交易日收盘）
            sell_idx = min(buy_idx + hold_days, len(df) - 1)
            sell_row = df.loc[sell_idx]
            sell_price = float(sell_row["收盘价"]) * (1 - self.slippage)

            # 净收益率（扣除双向手续费）
            gross_return = (sell_price - buy_price) / buy_price
            net_return = gross_return - 2 * self.commission

            return {
                "code": code,
                "select_date": select_date.strftime("%Y-%m-%d"),
                "buy_date": buy_row["日期"].strftime("%Y-%m-%d"),
                "sell_date": sell_row["日期"].strftime("%Y-%m-%d"),
                "buy_price": round(buy_price, 4),
                "sell_price": round(sell_price, 4),
                "gross_return": round(gross_return, 6),
                "net_return": round(net_return, 6),
                "hold_days": sell_idx - buy_idx,
            }
        except Exception as e:
            self.logger.warning(f"{code} 回测异常: {e}")
            return None

    # ------------------------------------------------------------------
    # 汇总统计
    # ------------------------------------------------------------------
    @staticmethod
    def _summarize(trades: list[dict]) -> dict:
        if not trades:
            return {
                "total": 0,
                "win_count": 0,
                "win_rate": 0.0,
                "avg_return": 0.0,
                "max_return": 0.0,
                "min_return": 0.0,
                "max_drawdown": 0.0,
                "trades": [],
            }

        returns = [t["net_return"] for t in trades]
        win_count = sum(1 for r in returns if r > 0)
        avg_ret = sum(returns) / len(returns)

        # 累计净值（等权，不做实际资金模拟）
        nav = 1.0
        peak = 1.0
        max_dd = 0.0
        for r in returns:
            nav *= (1 + r)
            peak = max(peak, nav)
            dd = (peak - nav) / peak
            max_dd = max(max_dd, dd)

        return {
            "total": len(trades),
            "win_count": win_count,
            "win_rate": round(win_count / len(trades), 4),
            "avg_return": round(avg_ret, 6),
            "max_return": round(max(returns), 6),
            "min_return": round(min(returns), 6),
            "max_drawdown": round(max_dd, 6),
            "trades": trades,
        }

    # ------------------------------------------------------------------
    # 报告打印
    # ------------------------------------------------------------------
    @staticmethod
    def print_report(report: dict) -> None:
        print("\n" + "=" * 60)
        print("回测报告")
        print("=" * 60)
        if report["total"] == 0:
            print("没有有效交易记录，无法生成报告。")
            return

        print(f"总交易次数  : {report['total']}")
        print(f"盈利次数    : {report['win_count']}")
        print(f"胜率        : {report['win_rate']:.2%}")
        print(f"平均收益率  : {report['avg_return']:.2%}")
        print(f"最大单次收益: {report['max_return']:.2%}")
        print(f"最小单次收益: {report['min_return']:.2%}")
        print(f"最大策略回撤: {report['max_drawdown']:.2%}")
        print("-" * 60)
        print(f"{'代码':<8} {'买入日':<12} {'卖出日':<12} {'买价':>8} {'卖价':>8} {'净收益':>9}")
        for t in report["trades"]:
            ret_str = f"{t['net_return']:+.2%}"
            print(
                f"{t['code']:<8} {t['buy_date']:<12} {t['sell_date']:<12} "
                f"{t['buy_price']:>8.3f} {t['sell_price']:>8.3f} {ret_str:>9}"
            )
        print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # 保存结果
    # ------------------------------------------------------------------
    @staticmethod
    def save_report(report: dict, filepath: str = "data/backtest_results.csv") -> None:
        """将交易明细保存到 CSV。"""
        if not report["trades"]:
            logger.warning("回测交易列表为空，未保存")
            return
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame(report["trades"])
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"回测明细已保存到 {filepath}")

    # ------------------------------------------------------------------
    # 因子贡献度评估（按规则分组）
    # ------------------------------------------------------------------
    @staticmethod
    def factor_attribution(stocks: list[dict], trades: list[dict]) -> dict:
        """按规则 passed/failed 分组统计平均收益，用于评估每个因子的有效性。

        Args:
            stocks: 选股结果列表，每项必须含 ``code`` 和 ``rules`` 字段
                    （rules 形如 {"主力资金":{"passed":True}, ...}）。
            trades: 由 run() 产出的 trades 明细。

        Returns:
            dict[rule_name] -> {n_pass, n_fail, ret_pass, ret_fail, ic_proxy}
        """
        # code -> net_return
        ret_map = {t["code"]: t["net_return"] for t in trades}

        rule_names = set()
        for s in stocks:
            rule_names.update((s.get("rules") or {}).keys())

        result = {}
        for rn in rule_names:
            pass_rets, fail_rets = [], []
            for s in stocks:
                code = s.get("code") or s.get("代码")
                r = ret_map.get(code)
                if r is None:
                    continue
                ru = (s.get("rules") or {}).get(rn)
                if not ru:
                    continue
                if ru.get("passed"):
                    pass_rets.append(r)
                else:
                    fail_rets.append(r)

            n_p, n_f = len(pass_rets), len(fail_rets)
            avg_p = sum(pass_rets) / n_p if n_p else 0.0
            avg_f = sum(fail_rets) / n_f if n_f else 0.0
            result[rn] = {
                "n_pass": n_p,
                "n_fail": n_f,
                "ret_pass": round(avg_p, 6),
                "ret_fail": round(avg_f, 6),
                "spread"  : round(avg_p - avg_f, 6),  # 多空收益差，>0 即因子正向有效
            }
        return result

    @staticmethod
    def print_factor_attribution(attribution: dict) -> None:
        if not attribution:
            print("没有可分析的因子样本。")
            return
        print("\n" + "=" * 72)
        print("因子贡献度（多空收益差，>0 表示因子正向有效）")
        print("=" * 72)
        print(f"{'规则':<14} {'通过数':>6} {'未过数':>6} "
              f"{'通过均收':>10} {'未过均收':>10} {'多空差':>10}")
        # 按 spread 降序
        items = sorted(attribution.items(), key=lambda kv: kv[1]["spread"], reverse=True)
        for name, m in items:
            print(
                f"{name:<14} {m['n_pass']:>6} {m['n_fail']:>6} "
                f"{m['ret_pass']:>+10.2%} {m['ret_fail']:>+10.2%} {m['spread']:>+10.2%}"
            )
        print("=" * 72 + "\n")
