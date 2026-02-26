"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from logger import get_logger

logger = get_logger(__name__)

class TechnicalIndicator:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(df, period):
        """计算移动平均线
        
        Args:
            df: 数据框
            period: 周期
            
        Returns:
            Series: MA值
        """
        return df['收盘价'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_macd(df, fast=12, slow=26, signal=9):
        """计算 MACD 指标
        
        Args:
            df: 数据框
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            DataFrame: 包含 DIF, DEA, MACD 列
        """
        close = df['收盘价']
        exp1 = close.ewm(span=fast).mean()
        exp2 = close.ewm(span=slow).mean()
        dif = exp1 - exp2
        dea = dif.ewm(span=signal).mean()
        macd = 2 * (dif - dea)
        
        result = pd.DataFrame({
            'DIF': dif,
            'DEA': dea,
            'MACD': macd
        })
        return result
    
    @staticmethod
    def check_golden_cross(df, ma_short=5, ma_long=10):
        """检查是否形成金叉（短期MA > 长期MA）
        
        Args:
            df: 数据框
            ma_short: 短期MA周期
            ma_long: 长期MA周期
            
        Returns:
            bool: 是否形成金叉
        """
        if len(df) < ma_long + 1:
            return False
        
        ma_short_series = TechnicalIndicator.calculate_ma(df, ma_short)
        ma_long_series = TechnicalIndicator.calculate_ma(df, ma_long)
        
        # 获取最后两条记录
        # 当前是否满足金叉条件：短期MA > 长期MA
        current_cross = ma_short_series.iloc[-1] > ma_long_series.iloc[-1]
        
        # 前一条是否满足条件
        prev_cross = ma_short_series.iloc[-2] <= ma_long_series.iloc[-2]
        
        # 金叉：从上方或相等穿越到下方变为上方穿越
        is_golden_cross = current_cross and (not prev_cross or ma_short_series.iloc[-2] <= ma_long_series.iloc[-2])
        
        # 更宽松的判断：只要当前短期MA > 长期MA即可
        # return current_cross
        
        logger.debug(f"金叉检查: current_cross={current_cross}, 最新MA5={ma_short_series.iloc[-1]:.2f}, 最新MA10={ma_long_series.iloc[-1]:.2f}")
        return current_cross  # 使用宽松判断，只要MA5 > MA10即认为是金叉状态

class StockAnalyzer:
    """股票分析器"""
    
    @staticmethod
    def check_limit_up_days(df, days=15, threshold=0.095):
        """检查最近N个交易日是否有涨停
        
        Args:
            df: 日线数据框，按日期升序排列
            days: 检查天数
            threshold: 涨停阈值（默认9.5%）
            
        Returns:
            tuple: (是否有涨停, 涨停日期列表, 最大涨幅)
        """
        if len(df) < 2:
            return False, [], 0
        
        # 获取最近N个交易日的数据
        recent_df = df.tail(days).copy()
        
        # 计算涨幅（相对前日收盘价）
        recent_df['日收益率'] = (recent_df['收盘价'] - recent_df['收盘价'].shift(1)) / recent_df['收盘价'].shift(1)
        
        # 查找涨停
        limit_ups = recent_df[recent_df['日收益率'] >= threshold]
        
        if len(limit_ups) > 0:
            limit_up_dates = limit_ups['日期'].tolist()
            max_increase = recent_df['日收益率'].max()
            logger.debug(f"发现涨停: {len(limit_ups)} 个，最大涨幅 {max_increase:.2%}")
            return True, limit_up_dates, max_increase
        
        max_increase = recent_df['日收益率'].max()
        logger.debug(f"未发现涨停，最大涨幅 {max_increase:.2%}")
        return False, [], max_increase
    
    @staticmethod
    def check_volume_multiple(df, days=5, ratio=2.0, avg_period=20):
        """检查最近N个交易日是否有倍量交易
        
        Args:
            df: 日线数据框，按日期升序排列
            days: 检查天数
            ratio: 倍数（成交量是前20日平均的多少倍）
            avg_period: 用于计算平均成交量的周期
            
        Returns:
            tuple: (是否有倍量, 倍量日期列表, 最大倍数)
        """
        if len(df) < avg_period + days:
            logger.warning(f"数据不足: 需要至少 {avg_period + days} 条记录，实际 {len(df)} 条")
            return False, [], 0
        
        # 获取最近N个交易日
        recent_df = df.tail(days).copy()
        
        # 计算平均成交量（前20日）
        avg_volume = df.iloc[-(avg_period + days):-days]['成交量'].mean()
        
        if avg_volume == 0:
            logger.warning("平均成交量为0")
            return False, [], 0
        
        # 检查倍量
        recent_df['倍数'] = recent_df['成交量'] / avg_volume
        volume_multiples = recent_df[recent_df['倍数'] >= ratio]
        
        if len(volume_multiples) > 0:
            volume_dates = volume_multiples['日期'].tolist()
            max_multiple = recent_df['倍数'].max()
            logger.debug(f"发现倍量交易: {len(volume_multiples)} 个，最大倍数 {max_multiple:.2f}x")
            return True, volume_dates, max_multiple
        
        max_multiple = recent_df['倍数'].max()
        logger.debug(f"未发现倍量交易，最大倍数 {max_multiple:.2f}x")
        return False, [], max_multiple
    
    @staticmethod
    def is_st_stock(code):
        """判断是否为ST股票
        
        Args:
            code: 股票代码
            
        Returns:
            bool: 是否为ST股票
        """
        return code.startswith('ST') or code.startswith('*')

class IndicatorCalculator:
    """指标计算器（包装类）"""
    
    def __init__(self, daily_df, weekly_df=None):
        """初始化
        
        Args:
            daily_df: 日线数据框
            weekly_df: 周线数据框（可选）
        """
        self.daily_df = daily_df
        self.weekly_df = weekly_df
        self.logger = get_logger(__name__)
    
    def calculate_all(self):
        """计算所有指标"""
        result = {}
        
        # 周线金叉
        if self.weekly_df is not None and len(self.weekly_df) >= 11:
            result['weekly_golden_cross'] = TechnicalIndicator.check_golden_cross(
                self.weekly_df, ma_short=5, ma_long=10
            )
        else:
            self.logger.warning("周线数据不足，无法检查金叉")
            result['weekly_golden_cross'] = False
        
        # 日线金叉（作为参考）
        if len(self.daily_df) >= 11:
            result['daily_golden_cross'] = TechnicalIndicator.check_golden_cross(
                self.daily_df, ma_short=5, ma_long=10
            )
        else:
            result['daily_golden_cross'] = False
        
        # 涨停检查
        result['has_limit_up'], result['limit_up_dates'], result['max_increase'] = \
            StockAnalyzer.check_limit_up_days(self.daily_df, days=15, threshold=0.095)
        
        # 倍量检查
        result['has_volume_multiple'], result['volume_dates'], result['max_multiple'] = \
            StockAnalyzer.check_volume_multiple(self.daily_df, days=5, ratio=2.0, avg_period=20)
        
        return result
