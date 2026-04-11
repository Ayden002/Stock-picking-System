"""
统一 CLI 入口 - 量化选股框架

用法：
    python cli.py select              # 运行选股（全量 A 股）
    python cli.py select --sample 50  # 快速测试（前50只）
    python cli.py select --codes 000001 000002

    python cli.py backtest            # 对最近一次选股结果做回测
    python cli.py backtest --hold 10  # 持有 10 个交易日

    python cli.py portfolio           # 打印最近选股结果的仓位分配方案
    python cli.py portfolio --capital 200000  # 指定 20 万资金

运行结果：
    data/stock_filter_results.csv   - 选股明细
    data/backtest_results.csv       - 回测明细
    logs/quant_YYYYMMDD.log         - 运行日志
"""
import sys
import io
import argparse

# ── Windows UTF-8 ──────────────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
# ──────────────────────────────────────────────────────────────────────────

import time
import os
import pandas as pd
from datetime import datetime

from logger import get_logger
from config import STOCK_LIST, BACKTEST_CONFIG, PORTFOLIO_CONFIG

logger = get_logger(__name__)


# ===========================================================================
# select 子命令
# ===========================================================================
def cmd_select(args):
    """运行选股"""
    from stock_selector import get_recommended_stocks

    _print_banner("选股模式")

    codes = args.codes if args.codes else (STOCK_LIST if STOCK_LIST else None)

    t0 = time.time()
    passed, all_results = get_recommended_stocks(codes, args.sample)
    elapsed = time.time() - t0

    _print_select_results(passed, all_results)
    print(f"\n⏱  耗时：{elapsed:.1f} 秒")
    print(f"📄 结果文件：data/stock_filter_results.csv")
    print(f"📋 日志目录：logs/\n")
    return 0 if passed else 1


# ===========================================================================
# backtest 子命令
# ===========================================================================
def cmd_backtest(args):
    """对选股结果做持有回测"""
    from data_fetcher import DataFetcher
    from backtest import BacktestEngine

    result_file = "data/stock_filter_results.csv"
    if not os.path.exists(result_file):
        print(f"[ERR] 找不到选股结果文件 {result_file}，请先运行 `python cli.py select`")
        return 1

    df = pd.read_csv(result_file, encoding="utf-8-sig")
    # 只取通过筛选的股票
    if "通过筛选" in df.columns:
        df = df[df["通过筛选"] == "是"]

    if df.empty:
        print("[--] 没有通过筛选的股票，无法回测")
        return 1

    stocks = []
    date_col = "选股日期" if "选股日期" in df.columns else "日期"
    for _, row in df.iterrows():
        stocks.append({
            "code": str(row["代码"]).zfill(6),
            "select_date": str(row.get(date_col, "")),
        })

    _print_banner("回测模式")
    hold = args.hold or BACKTEST_CONFIG["hold_days"]
    print(f"持有天数：{hold} 个交易日")
    print(f"参与回测股票：{len(stocks)} 只\n")

    fetcher = DataFetcher()
    engine = BacktestEngine(
        fetcher,
        hold_days=hold,
        commission=BACKTEST_CONFIG["commission"],
        slippage=BACKTEST_CONFIG["slippage"],
    )
    report = engine.run(stocks, hold_days=hold)
    engine.print_report(report)
    engine.save_report(report)
    print(f"📄 回测明细：data/backtest_results.csv\n")
    return 0


# ===========================================================================
# portfolio 子命令
# ===========================================================================
def cmd_portfolio(args):
    """打印仓位分配方案"""
    from portfolio import PortfolioManager

    result_file = "data/stock_filter_results.csv"
    if not os.path.exists(result_file):
        print(f"[ERR] 找不到选股结果文件 {result_file}，请先运行 `python cli.py select`")
        return 1

    df = pd.read_csv(result_file, encoding="utf-8-sig")
    if "通过筛选" in df.columns:
        df = df[df["通过筛选"] == "是"]

    if df.empty:
        print("[--] 没有通过筛选的股票")
        return 1

    stocks = []
    price_col = "最新收盘价" if "最新收盘价" in df.columns else df.columns[2]
    for _, row in df.iterrows():
        stocks.append({
            "code": str(row["代码"]).zfill(6),
            "details": {"latest_close": float(row.get(price_col, 0))},
        })

    capital = args.capital if args.capital else PORTFOLIO_CONFIG["total_capital"]
    max_pos = args.max_positions if args.max_positions else PORTFOLIO_CONFIG["max_positions"]

    _print_banner("组合分配")
    pm = PortfolioManager(
        max_positions=max_pos,
        total_capital=capital,
        stop_loss=PORTFOLIO_CONFIG["stop_loss"],
        take_profit=PORTFOLIO_CONFIG["take_profit"],
        min_position_pct=PORTFOLIO_CONFIG["min_position_pct"],
        max_position_pct=PORTFOLIO_CONFIG["max_position_pct"],
    )
    allocation = pm.allocate(stocks)
    pm.print_allocation(allocation)

    print(f"风控参数：止损 -{PORTFOLIO_CONFIG['stop_loss']:.0%}  |  "
          f"止盈 +{PORTFOLIO_CONFIG['take_profit']:.0%}")
    return 0


# ===========================================================================
# 辅助打印
# ===========================================================================
def _print_banner(mode: str):
    print("\n" + "=" * 60)
    print(f"       量化选股框架  ·  {mode}")
    print("=" * 60 + "\n")


def _print_select_results(passed, all_results):
    print("\n" + "=" * 60)
    print("选股结果")
    print("=" * 60 + "\n")

    if passed:
        print(f"✅ 发现 {len(passed)} 只符合条件的股票：\n")
        for i, s in enumerate(passed, 1):
            d = s["details"]
            print(f"  {i:>2}. {s['code']}  收盘价 ¥{d['latest_close']:.2f}"
                  f"  日期 {d['latest_date']}")
            for rule_name, rule_res in s.get("rules", {}).items():
                status = "✓" if rule_res["passed"] else "✗"
                print(f"        {status} {rule_name}")
            print()
    else:
        print("  未发现符合条件的股票\n")

    total = len(all_results)
    n_pass = len(passed)
    rate = n_pass / total * 100 if total else 0
    print(f"检查总数：{total}  通过：{n_pass}  通过率：{rate:.2f}%")


# ===========================================================================
# 主入口
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="量化选股框架 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # ── select ──────────────────────────────────────────────────────────────
    p_sel = sub.add_parser("select", help="运行选股")
    p_sel.add_argument("--codes", nargs="+", help="指定股票代码（空格分隔）")
    p_sel.add_argument("--sample", type=int, help="仅处理前 N 只股票（测试用）")

    # ── backtest ─────────────────────────────────────────────────────────────
    p_bt = sub.add_parser("backtest", help="对最近选股结果做持有回测")
    p_bt.add_argument("--hold", type=int, help=f"持有交易日数（默认 {BACKTEST_CONFIG['hold_days']}）")

    # ── portfolio ─────────────────────────────────────────────────────────────
    p_pt = sub.add_parser("portfolio", help="打印仓位分配方案")
    p_pt.add_argument("--capital", type=float, help="总资金（元）")
    p_pt.add_argument("--max-positions", dest="max_positions", type=int, help="最大持仓数")

    args = parser.parse_args()

    if args.command == "select":
        return cmd_select(args)
    elif args.command == "backtest":
        return cmd_backtest(args)
    elif args.command == "portfolio":
        return cmd_portfolio(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
