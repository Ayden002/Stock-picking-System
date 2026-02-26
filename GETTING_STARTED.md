# 使用入门指南

**新用户必读** ⚡

## 第一步：安装 Python

如果您还没有安装 Python，请先安装：

### Windows 用户
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.9 或更高版本
3. 运行安装程序
4. **重要**: 勾选 "Add Python to PATH"

### Mac 用户
```bash
brew install python3
```

### Linux 用户
```bash
sudo apt-get install python3 python3-pip
```

验证安装：
```bash
python --version
# 或
python3 --version
```

## 第二步：安装依赖包

进入项目目录，运行：

### Windows
```bash
pip install -r requirements.txt
```

### Mac/Linux
```bash
pip3 install -r requirements.txt
```

## 第三步：首次运行

### ✅ 最简单的方式

#### Windows 用户
双击 `run.bat` 文件

#### Mac/Linux 用户
```bash
chmod +x run.sh  # 首次需要
./run.sh
```

### 👆 第一次建议用测试模式

为了节省时间和流量，首次运行建议使用测试模式：

```bash
python main.py --sample 50
```

这会检查前50个股票，让您快速了解系统的工作流程。

## 第四步：查看结果

### 方式1：打开菜单查看

```bash
python tools.py
```

选择 "查看最新筛选结果"

### 方式2：直接查看文件

打开 `data/stock_filter_results.csv`

### 方式3：分析具体股票

```bash
python analyze.py 000001
```

## 常用命令速查表

| 操作 | 命令 | 说明 |
|------|------|------|
| 完整选股 | `python main.py` | 检查全部A股，可能需要长时间 |
| 快速测试 | `python main.py --sample 50` | 只检查50个股票，快速了解 |
| 指定股票 | `python main.py --codes 000001 000858` | 只检查指定的股票 |
| 打开菜单 | `python tools.py` | 交互式菜单工具 |
| 分析股票 | `python analyze.py 000001` | 对某个股票深度分析 |
| 运行测试 | `python test_system.py` | 系统功能测试 |

## ⏱️ 时间预期

- **测试模式** (50个股票): 约 2-5 分钟
- **小规模** (100-200个股票): 约 10-20 分钟
- **完整选股** (全部A股4000+个): 约 2-4 小时

💡 建议：首次运行使用测试模式，熟悉系统后再运行完整选股。

## 📊 期望结果

运行成功后，您会看到：

1. **控制台输出**
   ```
   = 选股结果 =
   发现 X 个符合条件的股票：
   1. 股票代码: 000001
      最新收盘价: ¥12.50
      最新日期: 2026-02-24
      周线金叉: ✓
   ...
   ```

2. **结果文件** `data/stock_filter_results.csv`
   - 包含所有检查的股票
   - 通过筛选的股票在前
   - 可用 Excel 或记事本打开

3. **日志文件** `logs/stock_selector_YYYYMMDD.log`
   - 详细的运行日志
   - 包含每个股票的处理过程

## 🎯 3个筛选条件说明

系统只会选出**同时满足以下三个条件**的股票：

### ✓ 周线金叉
- **是什么**: 周线的短期平均线（MA5）高于长期平均线（MA10）
- **为什么**: 表示股票进入上升趋势
- **示例**: 如果最近几周的股价趋势向上，则满足条件

### ✓ 15日内涨停
- **是什么**: 过去15个交易日中，至少有一天涨幅≥9.5%
- **为什么**: 表示股票最近表现强势
- **示例**: 股票在过去一个月内上涨超过10%的任何一天

### ✓ 5日内倍量
- **是什么**: 过去5个交易日中，至少有一天成交量是前20日平均的2倍
- **为什么**: 表示市场参与度突然增加，买家充足
- **示例**: 某一天成交量突然增加到平时的2倍以上

## 🔧 调整筛选条件

如果想改变筛选条件，编辑 `config.py` 文件：

```python
# 例如：改为周线 MA3 > MA8
'ma5_period': 3,
'ma10_period': 8,

# 例如：改为检查20日内涨停
'limit_up_days': 20,

# 例如：改为检查10日内倍量
'volume_multiple_days': 10,

# 例如：改为3倍量
'volume_multiple_ratio': 3.0,
```

修改后重新运行：
```bash
python main.py --sample 50
```

## 💻 系统要求

- **操作系统**: Windows、Mac、Linux
- **Python 版本**: 3.7 或更高
- **内存**: 至少 512MB
- **网络**: 需要互联网连接
- **磁盘**: 至少 100MB 可用空间

## ⚠️ 常见问题

### Q1: 运行时出现 "ModuleNotFoundError"

**原因**: 缺少必要的 Python 包

**解决**:
```bash
pip install -r requirements.txt
```

### Q2: 数据获取很慢或超时

**原因**: 网络问题或 AKshare 服务繁忙

**解决**:
- 检查网络连接
- 稍后重试
- 使用 `--sample` 参数进行小规模测试

### Q3: 显示 "未发现符合条件的股票"

**原因**: 当前市场中确实没有同时满足三个条件的股票

**解决**:
- 这是正常情况
- 可以放宽条件重新运行（编辑 `config.py`）
- 等待市场变化后重新筛选

### Q4: 某个股票显示无数据

**原因**: 该股票是新上市、已退市或被特殊处理

**解决**: 系统会自动跳过，无需处理

### Q5: Windows 上出现乱码

**原因**: 编码问题

**解决**: 使用 UTF-8 编码打开 CSV 文件
- 在 Excel 中打开
- 选择 "编码" → "UTF-8"

## 📈 下一步建议

1. **运行测试** (2-5分钟)
   ```bash
   python main.py --sample 50
   ```

2. **查看结果**
   ```bash
   python tools.py
   ```
   或直接打开 `data/stock_filter_results.csv`

3. **分析感兴趣的股票**
   ```bash
   python analyze.py 000001
   ```

4. **根据需要调整条件** (编辑 `config.py`)

5. **定期运行** (可配置自动定时)

## 📚 进阶学习

- **完整文档**: 查看 `README.md`
- **快速开始**: 查看 `QUICK_START.md`
- **系统架构**: 查看 `ARCHITECTURE.md`
- **项目完成说明**: 查看 `PROJECT_COMPLETION.md`

## ✅ 检查清单

使用前请确认：

- [ ] 已安装 Python 3.7+
- [ ] 已运行 `pip install -r requirements.txt`
- [ ] 网络连接正常
- [ ] 有足够的磁盘空间（至少 100MB）
- [ ] 已读过本文档

## 🚀 立即开始

### Windows
```bash
run.bat test
```

### Mac/Linux
```bash
./run.sh test
```

### 或任何系统
```bash
python main.py --sample 50
```

**预计等待时间**: 2-5 分钟

---

**需要帮助?** 查看完整文档或检查日志文件
