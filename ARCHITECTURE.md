# 项目架构和技术文档

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│              用户界面层                             │
├─────────────────────────────────────────────────────┤
│  main.py (主程序) │ tools.py (工具菜单) │ analyze.py│
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│              业务逻辑层                             │
├─────────────────────────────────────────────────────┤
│  stock_selector.py (选股筛选)                      │
└─────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│              技术指标层                              │
├──────────────────────────────────────────────────────┤
│  technical_indicator.py (金叉、涨停、倍量检测)      │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│              数据获取层                              │
├──────────────────────────────────────────────────────┤
│  data_fetcher.py (AKshare 接口)                    │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│              外部数据源                              │
├──────────────────────────────────────────────────────┤
│  AKshare 数据接口 (日线、周线数据)                  │
└──────────────────────────────────────────────────────┘
```

## 模块职责

### 核心模块

#### 1. `main.py` - 主程序入口
- **职责**: 程序入口，处理命令行参数
- **主要功能**:
  - 解析命令行参数
  - 调用选股逻辑
  - 输出结果和统计信息
  - 记录执行时间

#### 2. `data_fetcher.py` - 数据获取模块
- **职责**: 从 AKshare 获取股票数据
- **主要类**:
  - `DataFetcher`: 数据获取器
- **主要方法**:
  - `get_all_stock_codes()`: 获取所有 A 股代码
  - `get_stock_daily()`: 获取日线数据
  - `get_stock_weekly()`: 获取周线数据
  - `get_stock_info()`: 获取股票基本信息

#### 3. `technical_indicator.py` - 技术指标计算
- **职责**: 计算和检查各种技术指标
- **主要类**:
  - `TechnicalIndicator`: 技术指标计算类
  - `StockAnalyzer`: 股票分析器
  - `IndicatorCalculator`: 指标计算器
- **主要方法**:
  - `calculate_ma()`: 计算移动平均线
  - `calculate_macd()`: 计算 MACD
  - `check_golden_cross()`: 检查金叉
  - `check_limit_up_days()`: 检查涨停
  - `check_volume_multiple()`: 检查倍量

#### 4. `stock_selector.py` - 选股筛选模块
- **职责**: 执行选股筛选逻辑
- **主要类**:
  - `StockSelector`: 选股器
- **主要方法**:
  - `filter_stock()`: 对单个股票筛选
  - `filter_stocks_batch()`: 批量筛选
  - `save_results()`: 保存结果到 CSV
- **工作流程**:
  ```
  获取股票列表 → 逐个获取数据 → 计算指标 → 检查条件 → 
  → 保存结果 → 输出统计信息
  ```

#### 5. `config.py` - 配置文件
- **职责**: 集中管理所有配置参数
- **配置项**:
  - 选股条件参数
  - 日志配置
  - 数据超时和重试配置
  - 涨停阈值

#### 6. `logger.py` - 日志模块
- **职责**: 统一日志管理
- **功能**:
  - 输出到文件和控制台
  - 按日期创建日志文件
  - 格式化日志信息

### 辅助模块

#### 7. `tools.py` - 工具菜单
- **职责**: 提供交互式工具界面
- **功能**:
  - 查看最新结果
  - 导出结果
  - 统计分析
  - 快速分析

#### 8. `analyze.py` - 深度分析脚本
- **职责**: 对指定股票进行详细分析
- **功能**:
  - 趋势分析
  - 成交量分析
  - 技术指标详情

#### 9. `test_system.py` - 测试脚本
- **职责**: 系统功能测试
- **测试项**:
  - 数据获取测试
  - 技术指标测试
  - 批量选股测试

## 数据流

### 完整选股流程

```
1. 启动程序
   ↓
2. 解析命令行参数
   ↓
3. 初始化 DataFetcher
   ↓
4. 获取所有 A 股代码列表
   ↓
5. 循环处理每个股票:
   │
   ├→ 5.1 获取日线数据 (过去120天)
   │
   ├→ 5.2 获取周线数据 (过去52周)
   │
   ├→ 5.3 计算技术指标:
   │     - 周线金叉检测
   │     - 涨停检测 (15日)
   │     - 倍量检测 (5日)
   │
   ├→ 5.4 检查三个条件是否全部满足
   │
   └→ 5.5 保存结果
   ↓
6. 汇总统计信息
   ↓
7. 保存到 CSV 文件
   ↓
8. 输出结果和日志
```

## 算法详解

### 1. 周线金叉检测

**公式**:
- MA5 = (Close_today + Close_-1 + ... + Close_-4) / 5
- MA10 = (Close_today + Close_-1 + ... + Close_-9) / 10
- Golden Cross = MA5 > MA10

**代码**:
```python
def check_golden_cross(df, ma_short=5, ma_long=10):
    ma_short_series = df['收盘价'].rolling(window=ma_short).mean()
    ma_long_series = df['收盘价'].rolling(window=ma_long).mean()
    return ma_short_series.iloc[-1] > ma_long_series.iloc[-1]
```

### 2. 涨停检测

**条件**:
- 在过去 N 个交易日内
- 存在至少一个交易日涨幅 ≥ 阈值 (9.5%)

**公式**:
$$涨幅 = \frac{收盘价_今 - 收盘价_昨}{收盘价_昨}$$

**代码**:
```python
def check_limit_up_days(df, days=15, threshold=0.095):
    recent_df = df.tail(days).copy()
    recent_df['日收益率'] = (recent_df['收盘价'] - recent_df['收盘价'].shift(1)) / \
                             recent_df['收盘价'].shift(1)
    limit_ups = recent_df[recent_df['日收益率'] >= threshold]
    return len(limit_ups) > 0, limit_ups['日期'].tolist()
```

### 3. 倍量检测

**条件**:
- 在过去 N 个交易日内
- 存在至少一个交易日成交量 ≥ 前期平均的倍数

**公式**:
$$倍数 = \frac{成交量_今}{平均成交量_{前20日}}$$

**代码**:
```python
def check_volume_multiple(df, days=5, ratio=2.0, avg_period=20):
    recent_df = df.tail(days).copy()
    avg_volume = df.iloc[-(avg_period + days):-days]['成交量'].mean()
    recent_df['倍数'] = recent_df['成交量'] / avg_volume
    volume_multiples = recent_df[recent_df['倍数'] >= ratio]
    return len(volume_multiples) > 0, volume_multiples['日期'].tolist()
```

## 性能特性

### 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|-------|------|
| 获取股票列表 | O(1) | 一次性获取 |
| 获取单个股票数据 | O(N) | N = 数据天数 |
| 计算 MA | O(N) | 简单移动平均 |
| 涨停检测 | O(days) | days ≤ 15 |
| 倍量检测 | O(days) | days ≤ 5 |
| 单个股票筛选 | O(N) | 数据获取为主 |
| 批量筛选 | O(M×N) | M = 股票数，N = 数据天数 |

### 空间复杂度

| 数据结构 | 空间 | 说明 |
|---------|------|------|
| 日线数据 | O(120) | 保存120天数据 |
| 周线数据 | O(52) | 保存52周数据 |
| 结果列表 | O(M) | M = 通过筛选的股票数 |

### 优化建议

1. **数据缓存**: 使用本地数据库存储历史数据，减少网络请求
2. **并发处理**: 使用 ThreadPoolExecutor 进行并发数据获取
3. **增量更新**: 仅更新最近的数据而非全量获取
4. **批量接口**: 使用批量接口一次获取多个股票数据

## 错误处理

### 异常处理策略

```python
# 重试机制
for attempt in range(MAX_RETRIES):
    try:
        data = fetch_data()
        break
    except Exception as e:
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        else:
            logger.error(f"失败: {e}")
```

### 常见错误

| 错误类型 | 原因 | 处理 |
|---------|------|------|
| ConnectionError | 网络不可用 | 重试 + 记录 |
| Timeout | 数据获取超时 | 重试 + 增加超时 |
| ValueError | 数据格式错误 | 跳过 + 记录 |
| IndexError | 数据不足 | 跳过该股票 |

## 扩展性

### 如何添加新的技术指标

1. 在 `technical_indicator.py` 中的 `TechnicalIndicator` 类添加新方法:
```python
@staticmethod
def calculate_rsi(df, period=14):
    """计算 RSI 指标"""
    # 实现 RSI 逻辑
    return rsi_series
```

2. 在 `IndicatorCalculator.calculate_all()` 中调用:
```python
result['rsi'] = TechnicalIndicator.calculate_rsi(self.daily_df, period=14)
```

3. 在 `stock_selector.py` 中的条件检查中使用。

### 如何添加新的筛选条件

1. 在 `StockAnalyzer` 中添加新方法
2. 在 `IndicatorCalculator.calculate_all()` 中计算
3. 在 `StockSelector.filter_stock()` 中添加条件检查

## 部署建议

### 生产环境

- 使用 Docker 容器化部署
- 配置定时任务（Cron / 任务计划）
- 使用数据库存储结果历史
- 配置告警机制

### 开发环境

- 本地 Python 环境
- 虚拟环境隔离依赖
- IDE 调试

### 监控

- 定期检查日志文件
- 监控程序运行时间
- 记录筛选结果统计

---

**文档版本**: 1.0  
**最后更新**: 2026年2月26日
