#!/bin/bash

# 本地选股系统 - Linux/Mac 启动脚本
#
# 用法:
#   ./run.sh              # 运行完整选股
#   ./run.sh test         # 运行测试模式
#   ./run.sh tools        # 打开工具菜单

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "   本地智能选股系统 v1.0"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "✗ 错误: 未找到 Python"
        echo "请先安装 Python 3.7 或更高版本"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "使用 Python: $($PYTHON_CMD --version)"

# 检查依赖
if ! $PYTHON_CMD -c "import akshare" &> /dev/null; then
    echo "⚠ 首次运行，正在安装依赖包..."
    pip install -r requirements.txt
fi

# 创建必要的目录
mkdir -p data logs

# 执行对应命令
case "$1" in
    test)
        echo "运行测试模式（检查前50个股票）..."
        $PYTHON_CMD main.py --sample 50
        ;;
    tools)
        echo "打开工具菜单..."
        $PYTHON_CMD tools.py
        ;;
    analyze)
        if [ -z "$2" ]; then
            echo "用法: ./run.sh analyze <股票代码>"
            echo "例如: ./run.sh analyze 000001"
        else
            $PYTHON_CMD analyze.py "$2"
        fi
        ;;
    "")
        # 检查是否已有结果文件
        if [ -f "data/stock_filter_results.csv" ]; then
            echo ""
            read -p "检测到已有结果文件，是否覆盖？(Y/N): " confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                $PYTHON_CMD tools.py
                exit 0
            fi
        fi
        
        echo "运行完整选股（检查所有A股）..."
        echo "这可能需要较长时间，请耐心等待..."
        echo ""
        $PYTHON_CMD main.py
        ;;
    *)
        echo "用法: ./run.sh [命令] [参数]"
        echo ""
        echo "命令:"
        echo "  (无)        运行完整选股"
        echo "  test        运行测试模式 (检查前50个股票)"
        echo "  tools       打开工具菜单"
        echo "  analyze     分析指定股票"
        echo ""
        echo "示例:"
        echo "  ./run.sh"
        echo "  ./run.sh test"
        echo "  ./run.sh tools"
        echo "  ./run.sh analyze 000001"
        ;;
esac

echo ""
