@echo off
REM 本地选股系统 - Windows 启动脚本
REM
REM 用法:
REM   run.bat              # 运行完整选股
REM   run.bat test         # 运行测试模式
REM   run.bat tools        # 打开工具菜单

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ========================================
echo   本地智能选股系统 v1.0
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未找到 Python
    echo 请先安装 Python 3.7 或更高版本
    pause
    exit /b 1
)

REM 检查依赖
python -c "import akshare" >nul 2>&1
if errorlevel 1 (
    echo ⚠ 首次运行，正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ✗ 依赖安装失败
        pause
        exit /b 1
    )
)

REM 执行对应命令
if "%1"=="test" (
    echo 运行测试模式（检查前50个股票）...
    python main.py --sample 50
) else if "%1"=="tools" (
    echo 打开工具菜单...
    python tools.py
) else if "%1"=="analyze" (
    if "%2"=="" (
        echo 用法: run.bat analyze ^<股票代码^>
        echo 例如: run.bat analyze 000001
    ) else (
        python analyze.py %2
    )
) else if "%1"=="" (
    REM 检查是否已有结果文件
    if exist "data\stock_filter_results.csv" (
        echo.
        echo 检测到已有结果文件，是否覆盖？
        set /p confirm="(Y/N): "
        if /i not "!confirm!"=="Y" (
            python tools.py
            exit /b 0
        )
    )
    echo 运行完整选股（检查所有A股）...
    echo 这可能需要较长时间，请耐心等待...
    echo.
    python main.py
) else (
    echo 用法: run.bat [命令] [参数]
    echo.
    echo 命令:
    echo   (无)        运行完整选股
    echo   test        运行测试模式 (检查前50个股票)
    echo   tools       打开工具菜单
    echo   analyze     分析指定股票
    echo.
    echo 示例:
    echo   run.bat
    echo   run.bat test
    echo   run.bat tools
    echo   run.bat analyze 000001
)

echo.
pause
