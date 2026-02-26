"""
选股筛选模块
"""
import pandas as pd
from datetime import datetime
from logger import get_logger
from data_fetcher import DataFetcher
from technical_indicator import IndicatorCalculator

logger = get_logger(__name__)

class StockSelector:
    """股票选择器"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.logger = get_logger(__name__)
    
    def filter_stock(self, code):
        """对单个股票进行筛选
        
        Args:
            code: 股票代码
            
        Returns:
            dict: 包含筛选结果和详细信息的字典，或None如果筛选失败
        """
        try:
            self.logger.info(f"开始筛选股票 {code}")
            
            # 获取数据
            daily_df = self.fetcher.get_stock_daily(code, days=120)
            weekly_df = self.fetcher.get_stock_weekly(code, weeks=52)
            
            if daily_df is None or weekly_df is None:
                self.logger.warning(f"{code} 数据获取失败")
                return None
            
            if len(daily_df) < 30 or len(weekly_df) < 11:
                self.logger.warning(f"{code} 数据长度不足")
                return None
            
            # 计算指标
            calculator = IndicatorCalculator(daily_df, weekly_df)
            indicators = calculator.calculate_all()
            
            # 检查所有条件
            conditions = {
                'weekly_golden_cross': indicators['weekly_golden_cross'],
                'has_limit_up': indicators['has_limit_up'],
                'has_volume_multiple': indicators['has_volume_multiple'],
            }
            
            # 所有条件必须满足
            all_passed = all(conditions.values())
            
            result = {
                'code': code,
                'timestamp': datetime.now().isoformat(),
                'conditions': conditions,
                'passed': all_passed,
                'details': {
                    'latest_close': float(daily_df['收盘价'].iloc[-1]),
                    'latest_date': daily_df['日期'].iloc[-1].strftime('%Y-%m-%d'),
                    'weekly_golden_cross': indicators['weekly_golden_cross'],
                    'limit_up_dates': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in indicators['limit_up_dates']],
                    'max_increase': float(indicators['max_increase']),
                    'volume_dates': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in indicators['volume_dates']],
                    'max_multiple': float(indicators['max_multiple']),
                }
            }
            
            if all_passed:
                self.logger.info(f"✓ {code} 通过所有条件筛选")
            else:
                self.logger.debug(f"✗ {code} 未通过筛选: {conditions}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"{code} 筛选失败: {str(e)}", exc_info=True)
            return None
    
    def filter_stocks_batch(self, codes, max_workers=5):
        """批量筛选股票
        
        Args:
            codes: 股票代码列表
            max_workers: 最大并发数（保留用途，当前为顺序执行）
            
        Returns:
            list: 通过筛选的股票列表
        """
        results = []
        total = len(codes)
        
        self.logger.info(f"开始批量筛选 {total} 个股票")
        
        for i, code in enumerate(codes, 1):
            self.logger.info(f"[{i}/{total}] 正在处理 {code}")
            
            result = self.filter_stock(code)
            if result is not None:
                results.append(result)
        
        # 提取通过筛选的股票
        passed_stocks = [r for r in results if r['passed']]
        
        self.logger.info(f"筛选完成: 总共检查 {total} 个股票，{len(passed_stocks)} 个通过筛选")
        
        return passed_stocks, results
    
    def save_results(self, results, filename='stock_filter_results.csv'):
        """保存筛选结果到CSV文件
        
        Args:
            results: 筛选结果列表
            filename: 保存文件名
        """
        if not results:
            self.logger.warning("没有结果可保存")
            return
        
        try:
            # 构建 DataFrame
            data = []
            for r in results:
                data.append({
                    '代码': r['code'],
                    '日期': r['details']['latest_date'],
                    '最新收盘价': r['details']['latest_close'],
                    '周线金叉': '是' if r['details']['weekly_golden_cross'] else '否',
                    '涨停日期': ', '.join(r['details']['limit_up_dates']),
                    '最大涨幅': f"{r['details']['max_increase']:.2%}",
                    '倍量日期': ', '.join(r['details']['volume_dates']),
                    '最大倍数': f"{r['details']['max_multiple']:.2f}x",
                    '通过筛选': '是' if r['passed'] else '否',
                })
            
            df = pd.DataFrame(data)
            
            # 按通过筛选排序，通过的在前面
            df['通过筛选'] = df['通过筛选'] == '是'
            df = df.sort_values('通过筛选', ascending=False)
            df['通过筛选'] = df['通过筛选'].map({True: '是', False: '否'})
            
            filepath = f'data/{filename}'
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f"结果已保存到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}", exc_info=True)

def get_recommended_stocks(code_list=None, sample_size=None):
    """获取推荐的股票列表
    
    Args:
        code_list: 股票代码列表（如果为None则获取所有A股）
        sample_size: 样本大小（用于测试，获取前N个股票）
        
    Returns:
        tuple: (通过筛选的股票, 所有筛选结果)
    """
    selector = StockSelector()
    
    # 获取股票代码列表
    if code_list is None:
        codes = selector.fetcher.get_all_stock_codes()
    else:
        codes = code_list
    
    # 样本处理（用于测试）
    if sample_size is not None and len(codes) > sample_size:
        codes = codes[:sample_size]
        logger.info(f"仅处理前 {sample_size} 个股票进行测试")
    
    if not codes:
        logger.error("无法获取股票代码列表")
        return [], []
    
    # 筛选
    passed_stocks, all_results = selector.filter_stocks_batch(codes)
    
    # 保存结果
    selector.save_results(all_results)
    
    return passed_stocks, all_results
