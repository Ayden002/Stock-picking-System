# 量化选股框架

一个基于 Python + AKshare 的 **A 股量化选股框架**，面向个人用户本地运行。

**核心能力：**
- 可插拔的规则体系（金叉 / 涨停 / 倍量，支持自由组合与扩展）
- 统一配置中心（所有参数集中在 `config.py`，无需改动业务代码）
- 数据本地缓存（减少重复请求，加快二次运行速度）
- 基础回测模块（T+1 买入、持有 N 天、统计收益率/胜率/回撤）
- 基础组合风控（最大持仓数、等权分配、止损止盈）
- 统一 CLI 入口（`cli.py`）

---

## 目录结构

```
Stock-picking-System/
├── cli.py                   # ★ 统一 CLI 入口（推荐使用）
├── main.py                  # 原入口（保留，兼容旧用法）
├── config.py                # ★ 全局配置中心（参数全在这里）
├── logger.py                # 日志模块
├── data_fetcher.py          # 数据获取（AKshare + 本地缓存）
├── technical_indicator.py   # 技术指标计算（MA/MACD/金叉等）
├── stock_selector.py        # 选股引擎（调用 rules/ 里的规则）
├── analyze.py               # 单股深度分析脚本
├── test_system.py           # 功能自检脚本
├── requirements.txt         # 依赖列表
│
├── rules/                   # ★ 可插拔规则模块
│   ├── __init__.py
│   ├── base.py              # 规则基类（BaseRule）
│   ├── golden_cross.py      # 均线金叉规则
│   ├── limit_up.py          # 涨停规则
│   └── volume_spike.py      # 倍量规则
│
├── backtest/                # ★ 回测模块
│   ├── __init__.py
│   └── engine.py            # 简单持有回测引擎
│
├── portfolio/               # ★ 组合管理 / 风控模块
│   ├── __init__.py
│   └── manager.py           # 仓位分配 + 止损止盈
│
├── data/                    # 输出目录
│   ├── cache/               # 本地行情缓存（CSV，自动维护）
│   ├── stock_filter_results.csv  # 选股结果
│   └── backtest_results.csv      # 回测明细
│
└── logs/                    # 日志目录
    └── quant_YYYYMMDD.log
```

---

## 安装与运行

### 1. 环境要求

- Python 3.8+
- 可用的网络连接（首次运行需要从 AKshare 拉取数据）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行选股

```bash
# 全量 A 股（速度较慢，适合每天收盘后定时运行）
python cli.py select

# 快速测试：只检查前 50 只股票
python cli.py select --sample 50

# 检查指定股票
python cli.py select --codes 000001 000002 600036
```

### 4. 运行回测

先跑一次选股，再对结果做持有回测：

```bash
python cli.py select --sample 100

# 持有 5 个交易日（默认）
python cli.py backtest

# 持有 10 个交易日
python cli.py backtest --hold 10
```

### 5. 查看仓位分配

```bash
# 使用 config.py 里的默认资金
python cli.py portfolio

# 指定 20 万资金、最多持有 8 只
python cli.py portfolio --capital 200000 --max-positions 8
```

### 6. 单股深度分析

```bash
python analyze.py 000001
```

### 7. 旧版入口（兼容保留）

```bash
python main.py --sample 50
python main.py --codes 000001 000002
```

---

## 如何调整参数

所有参数集中在 **`config.py`**，修改后重新运行即可：

```python
# ── 规则参数 ──────────────────────────────────────────────
STOCK_FILTER_CONFIG = {
    'ma5_period'           : 5,     # 短期均线周期（改为 10 则用 MA10）
    'ma10_period'          : 10,    # 长期均线周期
    'use_weekly'           : True,  # True=周线金叉；False=日线金叉
    'limit_up_days'        : 15,    # 向前检查多少个交易日有涨停
    'limit_up_threshold'   : 0.095, # 涨停阈值（9.5%）
    'volume_multiple_days' : 5,     # 向前检查多少个交易日有倍量
    'volume_multiple_ratio': 2.0,   # 倍量倍数（2 倍均量）
    'volume_avg_period'    : 20,    # 基准均量的计算窗口
}

# ── 回测参数 ──────────────────────────────────────────────
BACKTEST_CONFIG = {
    'hold_days' : 5,       # 默认持有交易日数
    'commission': 0.0003,  # 单边手续费（万三）
    'slippage'  : 0.001,   # 单边滑点
}

# ── 组合风控参数 ──────────────────────────────────────────
PORTFOLIO_CONFIG = {
    'max_positions'   : 10,        # 最多持有几只
    'total_capital'   : 100_000.0, # 总资金（元）
    'stop_loss'       : 0.05,      # 止损线（跌幅）
    'take_profit'     : 0.10,      # 止盈线（涨幅）
    'max_position_pct': 0.20,      # 单票最大仓位
}

# ── 过滤选项 ──────────────────────────────────────────────
FILTER_OPTIONS = {
    'exclude_st'   : True,  # 过滤 ST / *ST
    'exclude_bj'   : False, # 是否过滤北交所
    'min_list_days': 60,    # 最短上市天数
}
```

---

## 如何新增规则/因子

1. **在 `rules/` 目录新建文件**，继承 `BaseRule`：

```python
# rules/rsi_filter.py
import pandas as pd
from rules.base import BaseRule

class RSIFilterRule(BaseRule):
    name = "RSI 超卖"

    def __init__(self, period: int = 14, threshold: float = 30.0):
        self.period = period
        self.threshold = threshold

    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None) -> dict:
        close = daily_df["收盘价"]
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(self.period).mean()
        loss = (-delta.clip(upper=0)).rolling(self.period).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi = 100 - 100 / (1 + rs)
        latest_rsi = float(rsi.iloc[-1])
        return {
            "passed": latest_rsi < self.threshold,
            "detail": {"rsi": round(latest_rsi, 2), "threshold": self.threshold},
        }
```

2. **在 `rules/__init__.py` 导出**（可选，方便外部 import）：

```python
from rules.rsi_filter import RSIFilterRule
```

3. **在 `cli.py` 或自定义脚本中使用**：

```python
from stock_selector import StockSelector
from rules import GoldenCrossRule, LimitUpRule, VolumeSpikeRule
from rules.rsi_filter import RSIFilterRule

# 组合四条规则
selector = StockSelector(rules=[
    GoldenCrossRule(),
    LimitUpRule(),
    VolumeSpikeRule(),
    RSIFilterRule(period=14, threshold=35),
])
```

---

## 如何运行回测

```bash
# 第一步：选出股票
python cli.py select --sample 100

# 第二步：对结果做持有 N 天回测
python cli.py backtest --hold 5
```

回测逻辑：
- 以选股日期 **T+1 开盘价**（含滑点）买入
- 持有 N 个交易日后以**收盘价**（含滑点）卖出
- 扣除双向手续费
- 统计：胜率、平均收益率、最大回撤

回测结果保存在 `data/backtest_results.csv`。

---

## 输出文件说明

| 文件 | 说明 |
|------|------|
| `data/stock_filter_results.csv` | 选股结果，包含每只股票的规则通过情况 |
| `data/backtest_results.csv` | 回测交易明细（买入日/卖出日/收益率等） |
| `data/cache/<code>_daily.csv` | 各股票日线行情本地缓存（自动维护，1 天过期） |
| `logs/quant_YYYYMMDD.log` | 当日运行日志 |

---

## 常见问题

**Q: 运行速度很慢怎么办？**
- 使用 `--sample 50` 先测试
- 在 `config.py` 的 `STOCK_LIST` 里指定关注的股票
- 本地缓存会在第二次运行时显著提速

**Q: 网络超时 / 接口失败？**
- 增大 `config.py` 中的 `REQUEST_TIMEOUT` 和 `MAX_RETRIES`
- AKshare 会自动切换备用数据源

**Q: 怎么只选主板股票？**
- 在 `config.py` 中设置 `FILTER_OPTIONS['exclude_bj'] = True`
- 并在 `STOCK_LIST` 里只填 000xxx / 600xxx 的代码

---

## 免责声明

本系统仅为技术工具，不构成投资建议。使用者自行承担投资风险。
数据来自 AKshare 接口，请在合法合规范围内使用。

---

**版本**: 2.0  ·  **更新**: 2026 年 4 月
