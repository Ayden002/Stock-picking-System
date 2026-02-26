"""
主程序入口
"""
import sys
import io
import time
import argparse

# 强制 stdout/stderr 使用 UTF-8（解决 Windows GBK 乱码）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from datetime import datetime
from logger import get_logger
from stock_selector import get_recommended_stocks
from config import STOCK_LIST

logger = get_logger(__name__)

def print_banner():
    """打印欢迎信息"""
    print("\n" + "="*60)
    print("         本地智能选股系统 v1.0")
    print("="*60)
    print("选股条件:")
    print("  1. 周线形成金叉（MA5 > MA10）")
    print("  2. 15个交易日内有过涨停（涨幅≥9.5%）")
    print("  3. 5个交易日内有倍量交易（成交量是前20日均值的2倍以上）")
    print("="*60 + "\n")

def run_selection(codes=None, sample_size=None):
    """运行选股
    
    Args:
        codes: 要检查的股票代码列表
        sample_size: 样本大小（用于测试）
    """
    try:
        logger.info("=" * 60)
        logger.info("开始选股流程")
        logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # 获取推荐股票
        passed_stocks, all_results = get_recommended_stocks(codes, sample_size)
        
        # 输出结果
        print("\n" + "="*60)
        print("选股结果")
        print("="*60 + "\n")
        
        if passed_stocks:
            print(f"[OK] 发现 {len(passed_stocks)} 个符合条件的股票:\n")
            
            for i, stock in enumerate(passed_stocks, 1):
                print(f"{i}. 股票代码: {stock['code']}")
                print(f"   最新收盘价: ¥{stock['details']['latest_close']:.2f}")
                print(f"   最新日期: {stock['details']['latest_date']}")
                print(f"   周线金叉: {'[OK]' if stock['details']['weekly_golden_cross'] else '[--]'}")
                if stock['details']['limit_up_dates']:
                    print(f"   涨停日期: {', '.join(stock['details']['limit_up_dates'])}")
                    print(f"   最大涨幅: {stock['details']['max_increase']:.2%}")
                if stock['details']['volume_dates']:
                    print(f"   倍量日期: {', '.join(stock['details']['volume_dates'])}")
                    print(f"   最大倍数: {stock['details']['max_multiple']:.2f}x")
                print()
        else:
            print("[--] 未发现符合条件的股票\n")
        
        # 统计信息
        print(f"检查总数: {len(all_results)} 个股票")
        print(f"通过筛选: {len(passed_stocks)} 个股票")
        if len(all_results) > 0:
            print(f"通过率: {len(passed_stocks)/len(all_results)*100:.2f}%")
        else:
            print("通过率: N/A")
        
        print("\n结果已保存到 data/stock_filter_results.csv")
        print(f"日志已保存到 logs/")
        
        logger.info("=" * 60)
        logger.info("选股流程完成")
        logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        return passed_stocks
        
    except Exception as e:
        logger.error(f"选股流程出错: {str(e)}", exc_info=True)
        print(f"\n[ERR] 选股失败: {str(e)}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='本地智能选股系统 - 基于AKshare数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py                          # 检查所有A股
  python main.py --codes 000001 000002     # 检查指定股票
  python main.py --sample 50               # 测试模式，检查前50个股票
        '''
    )
    
    parser.add_argument(
        '--codes',
        nargs='+',
        help='要检查的股票代码列表（不指定则检查所有A股）'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='样本大小（仅处理前N个股票，用于测试）'
    )
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print_banner()
    
    # 确定要检查的股票列表
    codes_to_check = args.codes if args.codes else (STOCK_LIST if STOCK_LIST else None)
    
    # 运行选股
    start_time = time.time()
    passed_stocks = run_selection(codes_to_check, args.sample)
    end_time = time.time()
    
    print(f"\n耗时: {end_time - start_time:.2f} 秒\n")
    
    if passed_stocks:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
