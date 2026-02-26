# 项目文件清单

## 📂 项目结构

```
stock/
│
├─ 📋 文档文件
│  ├─ README.md                 # ⭐ 完整项目文档（必读）
│  ├─ QUICK_START.md            # 快速开始指南（推荐先读）
│  ├─ GETTING_STARTED.md        # 使用入门指南（新手必读）
│  ├─ ARCHITECTURE.md           # 系统架构和技术文档
│  ├─ PROJECT_COMPLETION.md     # 项目完成说明
│  └─ FILES_MANIFEST.md         # 本文件
│
├─ 🐍 核心程序
│  ├─ main.py                   # 主程序入口
│  ├─ config.py                 # 配置文件（可自定义）
│  ├─ logger.py                 # 日志模块
│  ├─ data_fetcher.py           # 数据获取（AKshare）
│  ├─ technical_indicator.py    # 技术指标计算
│  └─ stock_selector.py         # 选股筛选逻辑
│
├─ 🛠️ 工具脚本
│  ├─ tools.py                  # 交互式菜单工具
│  ├─ analyze.py                # 股票分析脚本
│  └─ test_system.py            # 系统测试脚本
│
├─ 🚀 启动脚本
│  ├─ run.bat                   # Windows 启动脚本
│  └─ run.sh                    # Linux/Mac 启动脚本
│
├─ 📦 依赖管理
│  └─ requirements.txt          # Python 依赖列表
│
├─ 📁 数据目录
│  └─ data/                     # 输出结果文件目录
│     └─ stock_filter_results.csv  # 选股结果（自动生成）
│
└─ 📝 日志目录
   └─ logs/                     # 日志文件目录
      └─ stock_selector_*.log   # 每日日志（自动生成）
```

## 📄 文件详细说明

### 📋 文档文件

#### 1. **README.md** ⭐ 必读
- 项目完整文档
- 功能介绍
- 安装使用说明
- 常见问题解答
- 配置项说明
- **建议阅读时间**: 15-20分钟

#### 2. **QUICK_START.md** 推荐
- 快速上手指南
- 常用命令速查
- 性能优化提示
- 定时运行配置
- **建议阅读时间**: 5-10分钟

#### 3. **GETTING_STARTED.md** 新手必读
- 最基础的入门指南
- 逐步安装和运行
- 期望结果说明
- 常见问题速查
- **建议阅读时间**: 10-15分钟

#### 4. **ARCHITECTURE.md** 开发者参考
- 系统架构设计
- 模块职责详解
- 数据流详细说明
- 算法伪代码
- 性能分析
- **建议阅读时间**: 20-30分钟

#### 5. **PROJECT_COMPLETION.md** 项目总结
- 项目完成清单
- 功能列表
- 技术栈说明
- 使用场景说明
- **建议阅读时间**: 10分钟

#### 6. **FILES_MANIFEST.md** 本文件
- 所有文件的说明
- 快速查询工具
- **建议阅读时间**: 5分钟

### 🐍 核心程序文件

#### 1. **main.py** 主程序
```python
# 功能：程序入口
# 用途：解析命令行参数，调用选股逻辑
# 命令：
#   python main.py                    # 完整选股
#   python main.py --sample 50        # 快速测试
#   python main.py --codes 000001 000858  # 指定股票
```

#### 2. **config.py** 配置文件
```python
# 功能：集中管理所有配置
# 包含：
#   - 选股条件参数（MA周期、涨停天数等）
#   - 日志配置
#   - 网络超时设置
#   - 指定要检查的股票列表
# 修改：编辑这个文件可以自定义选股条件
```

#### 3. **logger.py** 日志模块
```python
# 功能：统一的日志管理
# 特性：
#   - 输出到文件和控制台
#   - 自动按日期创建日志文件
#   - 格式化日志信息
```

#### 4. **data_fetcher.py** 数据获取
```python
# 功能：从 AKshare 获取股票数据
# 类：DataFetcher
# 方法：
#   - get_all_stock_codes()    获取全部A股代码
#   - get_stock_daily()        获取日线数据
#   - get_stock_weekly()       获取周线数据
#   - get_stock_info()         获取基本信息
```

#### 5. **technical_indicator.py** 技术指标
```python
# 功能：计算各种技术指标
# 类：
#   - TechnicalIndicator       指标计算（MA、MACD等）
#   - StockAnalyzer           股票分析（金叉、涨停、倍量）
#   - IndicatorCalculator     指标计算器
# 主要算法：
#   - 移动平均线 (MA)
#   - 金叉检测
#   - 涨停检测
#   - 倍量检测
```

#### 6. **stock_selector.py** 选股筛选
```python
# 功能：执行选股筛选逻辑
# 类：StockSelector
# 方法：
#   - filter_stock()           单个股票筛选
#   - filter_stocks_batch()    批量筛选
#   - save_results()           保存结果到CSV
# 工作流程：获取数据 → 计算指标 → 检查条件 → 保存结果
```

### 🛠️ 工具脚本

#### 1. **tools.py** 菜单工具
```python
# 功能：交互式菜单工具
# 功能：
#   1. 查看最新筛选结果
#   2. 导出简单格式文本
#   3. 导出详细格式文本
#   4. 显示统计信息
#   5. 开始新的筛选
#   6. 对指定股票进行分析
# 用途：轻松查看和导出结果
```

#### 2. **analyze.py** 分析工具
```python
# 功能：对指定股票进行深度分析
# 命令：python analyze.py 000001
# 输出：
#   - 趋势分析（价格、MA、52周高低）
#   - 成交量分析
#   - 技术指标详情（金叉、涨停、倍量）
```

#### 3. **test_system.py** 测试脚本
```python
# 功能：系统功能测试
# 测试项：
#   1. 数据获取测试
#   2. 技术指标计算测试
#   3. 完整指标计算测试
#   4. 批量选股测试
# 用途：验证系统功能是否正常
```

### 🚀 启动脚本

#### 1. **run.bat** Windows启动脚本
```bash
# 使用方法：
#   双击运行              完整选股
#   run.bat test          测试模式（50个股票）
#   run.bat tools         打开工具菜单
#   run.bat analyze 000001   分析指定股票
```

#### 2. **run.sh** Linux/Mac启动脚本
```bash
# 使用方法：
#   chmod +x run.sh        # 首次需要
#   ./run.sh               完整选股
#   ./run.sh test          测试模式
#   ./run.sh tools         打开菜单
#   ./run.sh analyze 000001   分析股票
```

### 📦 依赖管理

#### **requirements.txt**
```
akshare>=1.14.0        # 股票数据接口
pandas>=1.3.0          # 数据处理
numpy>=1.21.0          # 数值计算
requests>=2.26.0       # HTTP 请求
python-dateutil>=2.8.2 # 日期处理
```

**安装方法**:
```bash
pip install -r requirements.txt
```

### 📁 输出文件

#### 1. **data/stock_filter_results.csv**
```csv
代码,日期,最新收盘价,周线金叉,涨停日期,最大涨幅,倍量日期,最大倍数,通过筛选
000001,2026-02-24,¥12.50,是,2026-02-24,10.05%,2026-02-23,2.15x,是
...
```

**说明**:
- 自动生成的筛选结果
- 通过筛选的股票在前面
- 可用 Excel 或文本编辑器打开

#### 2. **logs/stock_selector_YYYYMMDD.log**
```
2026-02-26 10:30:45 - stock_selector - INFO - 开始选股流程
2026-02-26 10:30:45 - data_fetcher - INFO - 开始获取所有A股股票代码...
...
```

**说明**:
- 每天生成一个日志文件
- 包含详细的运行信息
- 用于调试和记录

## 🗂️ 文件选择指南

### 我是新手，想快速上手
👉 推荐阅读顺序：
1. `GETTING_STARTED.md` (5-10分钟)
2. 运行 `python main.py --sample 50`
3. 查看 `data/stock_filter_results.csv`

### 我想了解完整的功能
👉 推荐阅读顺序：
1. `QUICK_START.md` (5分钟)
2. `README.md` (15分钟)
3. 实际运行系统

### 我是开发者，想理解架构
👉 推荐阅读顺序：
1. `README.md` 的"项目结构"部分
2. `ARCHITECTURE.md` (20分钟)
3. 查看源代码

### 我想修改选股条件
👉 推荐步骤：
1. 打开 `config.py`
2. 修改 `STOCK_FILTER_CONFIG`
3. 查看 `README.md` 中的配置说明
4. 运行测试

### 我想定时自动运行
👉 推荐阅读：
1. `QUICK_START.md` 中的"定时运行"部分
2. 使用 `run.bat` 或 `run.sh`

## 📊 文件大小参考

| 文件 | 大小 | 说明 |
|------|------|------|
| requirements.txt | < 1 KB | 依赖列表 |
| main.py | ~3 KB | 主程序 |
| config.py | ~2 KB | 配置 |
| data_fetcher.py | ~6 KB | 数据获取 |
| technical_indicator.py | ~8 KB | 指标计算 |
| stock_selector.py | ~7 KB | 选股逻辑 |
| tools.py | ~6 KB | 工具菜单 |
| analyze.py | ~5 KB | 分析工具 |
| test_system.py | ~5 KB | 测试脚本 |
| **文档总计** | ~100 KB | 所有 .md 文件 |
| **结果文件** | 变动 | stock_filter_results.csv |
| **日志文件** | 变动 | stock_selector_*.log |

## ⚡ 快速查询

### 我想要...

| 需求 | 文件 | 方法 |
|------|------|------|
| 快速开始 | GETTING_STARTED.md | 阅读 5 分钟 |
| 修改选股条件 | config.py | 编辑后重新运行 |
| 了解完整功能 | README.md | 阅读 15 分钟 |
| 查看选股结果 | data/ | 打开 CSV 文件 |
| 分析某个股票 | analyze.py | `python analyze.py 000001` |
| 打开菜单工具 | tools.py | `python tools.py` |
| 系统故障排查 | logs/ | 查看日志文件 |
| 理解系统架构 | ARCHITECTURE.md | 阅读 20 分钟 |

## ✅ 安装检查清单

安装后请确认：

- [ ] `requirements.txt` 存在
- [ ] 所有 6 个核心 .py 文件存在
- [ ] 所有 3 个工具 .py 文件存在
- [ ] 2 个启动脚本存在
- [ ] 6 个文档 .md 文件存在
- [ ] `data/` 目录存在
- [ ] `logs/` 目录存在

## 🔗 关键命令速查

```bash
# 安装依赖
pip install -r requirements.txt

# 快速测试
python main.py --sample 50

# 完整选股
python main.py

# 指定股票
python main.py --codes 000001 000858

# 打开菜单
python tools.py

# 分析股票
python analyze.py 000001

# 运行测试
python test_system.py

# Windows 启动
run.bat

# Mac/Linux 启动
./run.sh
```

---

**最后更新**: 2026年2月26日  
**项目版本**: 1.0  
**共包含**: 18 个文件 + 2 个目录
