"""
高级分析脚本 - 对已选中的股票进行深度分析
"""
import pandas as pd
from data_fetcher import DataFetcher
from technical_indicator import IndicatorCalculator, TechnicalIndicator
from logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class StockAnalyzerAdvanced:
    """高级股票分析器"""
    
    def __init__(self, code):
        """初始化
        
        Args:
            code: 股票代码
        """
        self.code = code
        self.fetcher = DataFetcher()
        self.logger = get_logger(__name__)
        self.daily_df = None
        self.weekly_df = None
    
    def load_data(self):
        """加载数据"""
        self.logger.info(f"加载 {self.code} 的数据...")
        self.daily_df = self.fetcher.get_stock_daily(self.code, days=250)
        self.weekly_df = self.fetcher.get_stock_weekly(self.code, weeks=104)
        
        if self.daily_df is None or self.weekly_df is None:
            self.logger.error(f"无法加载 {self.code} 的数据")
            return False
        return True
    
    def analyze_trend(self):
        """分析趋势"""
        if self.daily_df is None:
            return None
        
        latest = self.daily_df.iloc[-1]
        prev = self.daily_df.iloc[-2]
        
        # 计算MA
        ma5 = TechnicalIndicator.calculate_ma(self.daily_df, 5).iloc[-1]
        ma10 = TechnicalIndicator.calculate_ma(self.daily_df, 10).iloc[-1]
        ma20 = TechnicalIndicator.calculate_ma(self.daily_df, 20).iloc[-1]
        ma60 = TechnicalIndicator.calculate_ma(self.daily_df, 60).iloc[-1]
        
        return {
            'latest_close': latest['收盘价'],
            'latest_date': latest['日期'].strftime('%Y-%m-%d'),
            'change_pct': (latest['收盘价'] - prev['收盘价']) / prev['收盘价'],
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'ma60': ma60,
            'highest_52w': self.daily_df['最高价'].tail(250).max(),
            'lowest_52w': self.daily_df['最低价'].tail(250).min(),
        }
    
    def analyze_volume(self):
        """分析成交量"""
        if self.daily_df is None:
            return None
        
        recent_volume = self.daily_df['成交量'].tail(20)
        avg_volume = recent_volume.mean()
        latest_volume = recent_volume.iloc[-1]
        
        return {
            'latest_volume': latest_volume,
            'avg_volume_20d': avg_volume,
            'volume_ratio': latest_volume / avg_volume if avg_volume > 0 else 0,
        }
    
    def print_analysis_report(self):
        """打印分析报告"""
        if not self.load_data():
            print(f"✗ 无法加载 {self.code} 的数据")
            return
        
        print("\n" + "="*60)
        print(f"股票 {self.code} 深度分析报告")
        print("="*60)
        
        # 趋势分析
        trend = self.analyze_trend()
        print("\n【趋势分析】")
        print(f"  最新收盘价: ¥{trend['latest_close']:.2f}")
        print(f"  最新日期: {trend['latest_date']}")
        print(f"  日涨跌幅: {trend['change_pct']:+.2%}")
        print(f"\n  MA5: ¥{trend['ma5']:.2f}")
        print(f"  MA10: ¥{trend['ma10']:.2f}")
        print(f"  MA20: ¥{trend['ma20']:.2f}")
        print(f"  MA60: ¥{trend['ma60']:.2f}")
        print(f"\n  52周最高: ¥{trend['highest_52w']:.2f}")
        print(f"  52周最低: ¥{trend['lowest_52w']:.2f}")
        print(f"  52周涨幅: {(trend['latest_close'] - trend['lowest_52w']) / trend['lowest_52w']:+.2%}")
        
        # 成交量分析
        volume = self.analyze_volume()
        print("\n【成交量分析】")
        print(f"  最新成交量: {volume['latest_volume']:,.0f}")
        print(f"  20日均量: {volume['avg_volume_20d']:,.0f}")
        print(f"  倍数: {volume['volume_ratio']:.2f}x")
        
        # 技术指标
        if self.weekly_df is not None:
            calculator = IndicatorCalculator(self.daily_df, self.weekly_df)
            indicators = calculator.calculate_all()
            
            print("\n【技术指标】")
            print(f"  周线金叉(MA5>MA10): {'✓ 是' if indicators['weekly_golden_cross'] else '✗ 否'}")
            print(f"  日线金叉(MA5>MA10): {'✓ 是' if indicators['daily_golden_cross'] else '✗ 否'}")
            print(f"  15日涨停: {'✓ 是' if indicators['has_limit_up'] else '✗ 否'}")
            if indicators['has_limit_up']:
                print(f"    最大涨幅: {indicators['max_increase']:.2%}")
                for date in indicators['limit_up_dates'][:3]:
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    print(f"    - {date_str}")
            
            print(f"  5日倍量: {'✓ 是' if indicators['has_volume_multiple'] else '✗ 否'}")
            if indicators['has_volume_multiple']:
                print(f"    最大倍数: {indicators['max_multiple']:.2f}x")
                for date in indicators['volume_dates'][:3]:
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    print(f"    - {date_str}")
        
        print("\n" + "="*60 + "\n")

def analyze_stock(code):
    """分析单个股票"""
    analyzer = StockAnalyzerAdvanced(code)
    analyzer.print_analysis_report()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python analyze.py <股票代码>")
        print("例如: python analyze.py 000001")
        sys.exit(1)
    
    code = sys.argv[1]
    analyze_stock(code)
