"""
快速测试脚本 - 用于测试系统功能
"""
from data_fetcher import DataFetcher
from technical_indicator import IndicatorCalculator, TechnicalIndicator, StockAnalyzer
from logger import get_logger
import pandas as pd

logger = get_logger(__name__)

def test_data_fetcher():
    """测试数据获取"""
    print("\n" + "="*60)
    print("测试 1: 数据获取")
    print("="*60)
    
    fetcher = DataFetcher()
    
    # 测试获取某个股票的数据
    test_code = '000001'  # 平安银行
    print(f"\n获取 {test_code} 的数据...")
    
    daily_df = fetcher.get_stock_daily(test_code, days=50)
    if daily_df is not None:
        print(f"✓ 日线数据: {len(daily_df)} 条记录")
        print(daily_df.tail(3))
    else:
        print(f"✗ 日线数据获取失败")
    
    weekly_df = fetcher.get_stock_weekly(test_code, weeks=26)
    if weekly_df is not None:
        print(f"\n✓ 周线数据: {len(weekly_df)} 条记录")
        print(weekly_df.tail(3))
    else:
        print(f"✗ 周线数据获取失败")

def test_technical_indicator():
    """测试技术指标"""
    print("\n" + "="*60)
    print("测试 2: 技术指标计算")
    print("="*60)
    
    fetcher = DataFetcher()
    test_code = '000001'
    
    print(f"\n获取 {test_code} 的数据进行指标计算...")
    
    daily_df = fetcher.get_stock_daily(test_code, days=120)
    weekly_df = fetcher.get_stock_weekly(test_code, weeks=52)
    
    if daily_df is None or weekly_df is None:
        print("✗ 数据获取失败")
        return
    
    # 测试金叉
    print("\n周线金叉检测:")
    golden_cross = TechnicalIndicator.check_golden_cross(weekly_df, ma_short=5, ma_long=10)
    print(f"  结果: {'✓ 有金叉' if golden_cross else '✗ 无金叉'}")
    
    # 测试涨停
    print("\n涨停检测 (15日内):")
    has_limit_up, limit_up_dates, max_increase = StockAnalyzer.check_limit_up_days(daily_df, days=15)
    print(f"  有涨停: {'✓ 是' if has_limit_up else '✗ 否'}")
    print(f"  最大涨幅: {max_increase:.2%}")
    if limit_up_dates:
        for date in limit_up_dates:
            print(f"    - {date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else date}")
    
    # 测试倍量
    print("\n倍量检测 (5日内):")
    has_volume_multiple, volume_dates, max_multiple = StockAnalyzer.check_volume_multiple(daily_df, days=5, ratio=2.0)
    print(f"  有倍量: {'✓ 是' if has_volume_multiple else '✗ 否'}")
    print(f"  最大倍数: {max_multiple:.2f}x")
    if volume_dates:
        for date in volume_dates:
            print(f"    - {date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else date}")

def test_full_indicator_calculator():
    """测试完整指标计算"""
    print("\n" + "="*60)
    print("测试 3: 完整指标计算")
    print("="*60)
    
    fetcher = DataFetcher()
    test_code = '000001'
    
    print(f"\n对 {test_code} 进行完整指标计算...")
    
    daily_df = fetcher.get_stock_daily(test_code, days=120)
    weekly_df = fetcher.get_stock_weekly(test_code, weeks=52)
    
    if daily_df is None or weekly_df is None:
        print("✗ 数据获取失败")
        return
    
    calculator = IndicatorCalculator(daily_df, weekly_df)
    indicators = calculator.calculate_all()
    
    print("\n计算结果:")
    print(f"  周线金叉: {'✓' if indicators['weekly_golden_cross'] else '✗'}")
    print(f"  日线金叉: {'✓' if indicators['daily_golden_cross'] else '✗'}")
    print(f"  涨停: {'✓' if indicators['has_limit_up'] else '✗'}")
    print(f"  倍量: {'✓' if indicators['has_volume_multiple'] else '✗'}")
    print(f"  最大涨幅: {indicators['max_increase']:.2%}")
    print(f"  最大倍数: {indicators['max_multiple']:.2f}x")

def test_batch_selection():
    """测试批量选股"""
    print("\n" + "="*60)
    print("测试 4: 批量选股")
    print("="*60)
    
    from stock_selector import StockSelector
    
    print("\n对示例股票进行选股测试...")
    
    # 测试几个股票
    test_codes = ['000001', '000002', '000858', '000999', '600000']
    
    selector = StockSelector()
    results = []
    
    for code in test_codes:
        print(f"\n正在筛选 {code}...")
        result = selector.filter_stock(code)
        if result:
            results.append(result)
            status = '✓ 通过' if result['passed'] else '✗ 不通过'
            print(f"  {status}")
            print(f"  详情: {result['details']}")
    
    # 统计
    passed = [r for r in results if r['passed']]
    print(f"\n✓ 通过筛选: {len(passed)}/{len(results)}")

if __name__ == '__main__':
    try:
        print("\n开始系统测试...\n")
        
        test_data_fetcher()
        test_technical_indicator()
        test_full_indicator_calculator()
        # test_batch_selection()  # 注释此行以跳过较长的批量测试
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
