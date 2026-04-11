"""
系统自检脚本

涵盖：
  1. 规则模块单元测试（使用内置模拟数据，无需网络）
  2. 数据获取功能测试（需要网络，可跳过）
  3. 选股器集成测试（需要网络，可跳过）

运行方式：
    python test_system.py              # 只跑单元测试（不联网）
    python test_system.py --network    # 同时跑联网测试
"""
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger(__name__)


# ===========================================================================
# 辅助：生成模拟行情数据
# ===========================================================================
def _make_daily_df(n: int = 60, trend: float = 0.001,
                   has_limit_up: bool = False,
                   has_volume_spike: bool = False) -> pd.DataFrame:
    """生成 n 条模拟日线数据。"""
    base_price = 10.0
    prices = [base_price]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + trend + np.random.normal(0, 0.005)))

    if has_limit_up and n > 10:
        prices[-5] = prices[-6] * 1.10   # 在倒数第 5 天人工插入涨停

    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    # 使用固定成交量以保证测试确定性
    volumes = [1000.0] * n

    if has_volume_spike and n > 10:
        # 确保倒数第 3 天远超均量 × 2（1000 * 5 = 5000，均量 1000，倍数 5.0）
        volumes[-3] = 5000.0

    return pd.DataFrame({
        "日期": dates,
        "开盘价": prices,
        "收盘价": prices,
        "最高价": [p * 1.01 for p in prices],
        "最低价": [p * 0.99 for p in prices],
        "成交量": [float(v) for v in volumes],
        "成交额": [float(v) * p for v, p in zip(volumes, prices)],
        "振幅": [0.0] * n,
        "涨跌幅": [0.0] * n,
        "涨跌额": [0.0] * n,
        "换手率": [0.0] * n,
        "代码": ["000001"] * n,
    })


def _make_weekly_df(n: int = 20, golden: bool = True) -> pd.DataFrame:
    """生成模拟周线数据；golden=True 时 MA5 > MA10。"""
    if golden:
        # 上升趋势 → MA5 > MA10
        prices = [10.0 + i * 0.2 for i in range(n)]
    else:
        # 下降趋势 → MA5 < MA10
        prices = [10.0 + (n - i) * 0.2 for i in range(n)]

    dates = [datetime(2023, 1, 1) + timedelta(weeks=i) for i in range(n)]
    return pd.DataFrame({
        "日期": dates,
        "开盘价": prices,
        "收盘价": prices,
        "最高价": [p * 1.01 for p in prices],
        "最低价": [p * 0.99 for p in prices],
        "成交量": [1000.0] * n,
        "成交额": [1000.0 * p for p in prices],
        "振幅": [0.0] * n,
        "涨跌幅": [0.0] * n,
        "涨跌额": [0.0] * n,
        "换手率": [0.0] * n,
        "代码": ["000001"] * n,
    })


# ===========================================================================
# 单元测试
# ===========================================================================
def test_golden_cross_rule():
    print("\n[TEST 1] GoldenCrossRule")
    from rules import GoldenCrossRule

    rule = GoldenCrossRule(ma_short=5, ma_long=10, use_weekly=True)

    # 上升趋势周线 → 应当通过
    weekly_up = _make_weekly_df(golden=True)
    res = rule.evaluate(_make_daily_df(), weekly_up)
    assert res["passed"], f"上升趋势应通过金叉，实际: {res}"

    # 下降趋势周线 → 不应通过
    weekly_down = _make_weekly_df(golden=False)
    res = rule.evaluate(_make_daily_df(), weekly_down)
    assert not res["passed"], f"下降趋势不应通过金叉，实际: {res}"

    # 数据不足 → 不通过
    tiny = _make_weekly_df(n=5)
    res = rule.evaluate(_make_daily_df(), tiny)
    assert not res["passed"], "数据不足应返回 False"

    print("  ✓ GoldenCrossRule 测试通过")


def test_limit_up_rule():
    print("\n[TEST 2] LimitUpRule")
    from rules import LimitUpRule

    rule = LimitUpRule(days=15, threshold=0.095)

    daily_with    = _make_daily_df(n=60, has_limit_up=True)
    daily_without = _make_daily_df(n=60, has_limit_up=False, trend=0.0)

    res_with = rule.evaluate(daily_with)
    assert res_with["passed"], f"含涨停的数据应通过，实际: {res_with}"

    res_without = rule.evaluate(daily_without)
    # 由于随机噪声较小，绝大多数情况不会触发 9.5% 涨幅
    # （此处允许极小概率误差）
    print(f"  涨停结果: passed={res_without['passed']}, detail={res_without['detail']}")

    print("  ✓ LimitUpRule 测试通过")


def test_volume_spike_rule():
    print("\n[TEST 3] VolumeSpikeRule")
    from rules import VolumeSpikeRule

    rule = VolumeSpikeRule(days=5, ratio=2.0, avg_period=20)

    daily_with    = _make_daily_df(n=60, has_volume_spike=True)
    daily_without = _make_daily_df(n=60, has_volume_spike=False)

    res_with = rule.evaluate(daily_with)
    assert res_with["passed"], f"含倍量的数据应通过，实际: {res_with}"

    res_without = rule.evaluate(daily_without)
    print(f"  倍量结果: passed={res_without['passed']}, detail={res_without['detail']}")

    # 数据不足
    tiny = _make_daily_df(n=10)
    res_tiny = rule.evaluate(tiny)
    assert not res_tiny["passed"], "数据不足应返回 False"

    print("  ✓ VolumeSpikeRule 测试通过")


def test_backtest_engine():
    print("\n[TEST 4] BacktestEngine（使用模拟数据）")
    from unittest.mock import MagicMock
    from backtest import BacktestEngine

    daily = _make_daily_df(n=60, trend=0.002)

    fetcher = MagicMock()
    fetcher.get_stock_daily.return_value = daily

    engine = BacktestEngine(fetcher, hold_days=5, commission=0.0003, slippage=0.001)
    stocks = [{"code": "000001", "select_date": "2024-02-01"}]
    report = engine.run(stocks)

    assert "total" in report
    assert "win_rate" in report
    print(f"  报告: total={report['total']}, win_rate={report['win_rate']}")
    print("  ✓ BacktestEngine 测试通过")


def test_portfolio_manager():
    print("\n[TEST 5] PortfolioManager")
    from portfolio import PortfolioManager

    pm = PortfolioManager(max_positions=5, total_capital=100_000)
    stocks = [
        {"code": f"00000{i}", "details": {"latest_close": float(10 + i)}}
        for i in range(1, 8)
    ]
    allocation = pm.allocate(stocks)
    assert len(allocation) <= 5, "超过最大持仓数"
    for item in allocation:
        assert item["weight"] <= pm.max_position_pct
    pm.print_allocation(allocation)

    # 止损止盈
    assert pm.check_risk("000001", 10.0, 9.4) == "stop_loss"
    assert pm.check_risk("000001", 10.0, 11.1) == "take_profit"
    assert pm.check_risk("000001", 10.0, 10.3) == "hold"
    print("  ✓ PortfolioManager 测试通过")


def test_config():
    print("\n[TEST 6] config.py 参数一致性")
    from config import (
        STOCK_FILTER_CONFIG, BACKTEST_CONFIG, PORTFOLIO_CONFIG,
        FILTER_OPTIONS, CACHE_DIR, LOG_DIR,
    )
    import os
    assert os.path.isdir(CACHE_DIR), "CACHE_DIR 不存在"
    assert os.path.isdir(LOG_DIR), "LOG_DIR 不存在"
    assert "ma5_period" in STOCK_FILTER_CONFIG
    assert "hold_days" in BACKTEST_CONFIG
    assert "max_positions" in PORTFOLIO_CONFIG
    assert "exclude_st" in FILTER_OPTIONS
    print("  ✓ config.py 参数检查通过")


# ===========================================================================
# 联网测试（需要 --network 参数）
# ===========================================================================
def test_data_fetcher_network():
    print("\n[NET-TEST 1] DataFetcher（联网）")
    from data_fetcher import DataFetcher
    fetcher = DataFetcher()

    code = "000001"
    daily = fetcher.get_stock_daily(code, days=50)
    assert daily is not None and not daily.empty, "日线数据获取失败"
    print(f"  日线数据: {len(daily)} 条")

    weekly = fetcher.get_stock_weekly(code, weeks=26)
    assert weekly is not None and not weekly.empty, "周线数据获取失败"
    print(f"  周线数据: {len(weekly)} 条")
    print("  ✓ DataFetcher 联网测试通过")


def test_selector_network():
    print("\n[NET-TEST 2] StockSelector（联网）")
    from stock_selector import StockSelector
    selector = StockSelector()
    result = selector.filter_stock("000001")
    if result:
        status = "通过" if result["passed"] else "未通过"
        print(f"  000001 筛选结果: {status}")
        for rn, rv in result["rules"].items():
            print(f"    {'✓' if rv['passed'] else '✗'} {rn}")
    else:
        print("  数据获取失败（可能是网络问题）")
    print("  ✓ StockSelector 联网测试完成")


# ===========================================================================
# 主入口
# ===========================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true", help="同时运行联网测试")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("量化选股框架 - 系统自检")
    print("=" * 60)

    unit_tests = [
        test_config,
        test_golden_cross_rule,
        test_limit_up_rule,
        test_volume_spike_rule,
        test_backtest_engine,
        test_portfolio_manager,
    ]

    passed = 0
    failed = 0
    for fn in unit_tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {fn.__name__} 失败: {e}")
            failed += 1

    if args.network:
        print("\n--- 联网测试 ---")
        for fn in [test_data_fetcher_network, test_selector_network]:
            try:
                fn()
                passed += 1
            except Exception as e:
                print(f"  ✗ {fn.__name__} 失败: {e}")
                failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成：{passed} 通过，{failed} 失败")
    print("=" * 60 + "\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
