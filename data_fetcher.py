"""
数据获取模块 - 使用 Tushare Pro 接口，支持本地 CSV 缓存

缓存规则：
  - 日线数据按代码存储为 data/cache/<code>_daily.csv
  - 超过 CACHE_EXPIRE_DAYS 天（自然日）的缓存文件视为过期，重新拉取
  - 周线数据不单独缓存，由日线 resample 生成
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from logger import get_logger
from config import (
    MAX_RETRIES, RETRY_DELAY,
    CACHE_DIR, CACHE_EXPIRE_DAYS,
    TUSHARE_TOKEN,
)

logger = get_logger(__name__)

# 初始化 Tushare Pro
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

_DAILY_COLS = ['日期', '开盘价', '收盘价', '最高价', '最低价',
               '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
_WEEKLY_COLS = _DAILY_COLS


def _to_ts_code(code: str) -> str:
    """将6位代码转换为 Tushare 格式（如 600000 → 600000.SH）"""
    if code.startswith(('6', '9')):
        return code + '.SH'
    elif code.startswith(('0', '3')):
        return code + '.SZ'
    elif code.startswith(('4', '8')):
        return code + '.BJ'
    return code + '.SH'


class DataFetcher:
    """数据获取器（含本地 CSV 缓存）"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._daily_cache: dict = {}   # {code: DataFrame} 本次运行内存缓存

    # ------------------------------------------------------------------
    # 缓存辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _cache_path(code: str) -> str:
        return os.path.join(CACHE_DIR, f"{code}_daily.csv")

    @staticmethod
    def _cache_is_fresh(path: str) -> bool:
        """判断缓存文件是否在有效期内。"""
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return (datetime.now() - mtime).days < CACHE_EXPIRE_DAYS

    def _load_cache(self, code: str) -> pd.DataFrame | None:
        """从磁盘加载缓存的日线数据。"""
        path = self._cache_path(code)
        if not self._cache_is_fresh(path):
            return None
        try:
            df = pd.read_csv(path, encoding="utf-8")
            df["日期"] = pd.to_datetime(df["日期"])
            for col in ["开盘价", "收盘价", "最高价", "最低价"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            if "成交量" in df.columns:
                df["成交量"] = pd.to_numeric(df["成交量"], errors="coerce").fillna(0).astype(float)
            self.logger.debug(f"{code} 命中磁盘缓存")
            return df
        except Exception as e:
            self.logger.warning(f"{code} 读取缓存失败: {e}")
            return None

    def _save_cache(self, code: str, df: pd.DataFrame) -> None:
        """将日线数据写入磁盘缓存。"""
        try:
            df.to_csv(self._cache_path(code), index=False, encoding="utf-8")
        except Exception as e:
            self.logger.warning(f"{code} 写入缓存失败: {e}")

    # ------------------------------------------------------------------
    # 获取股票代码列表
    # ------------------------------------------------------------------
    def get_all_stock_codes(self):
        """获取所有A股上市股票代码（用最近交易日的 daily 全市场接口）"""
        self.logger.info("开始获取所有A股股票代码...")
        # 优先尝试 stock_basic（需要更高积分，升级后自动启用）
        try:
            df = pro.stock_basic(
                exchange='', list_status='L',
                fields='ts_code,symbol,name,list_date'
            )
            if df is not None and not df.empty:
                codes = df['symbol'].astype(str).str.zfill(6).tolist()
                codes = [c for c in codes if len(c) == 6 and c.isdigit()]
                self.logger.info(f"stock_basic 获取 {len(codes)} 个股票代码")
                return codes
        except Exception:
            pass

        # 备用：用最近交易日的 daily 接口获取全量代码
        self.logger.info("stock_basic 不可用，改用 daily 全市场接口获取代码")
        for days_back in range(1, 8):
            trade_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
            try:
                df = pro.daily(trade_date=trade_date)
                if df is not None and not df.empty:
                    # ts_code 格式如 "600000.SH"，提取前6位数字
                    codes = df['ts_code'].str[:6].tolist()
                    codes = [c for c in codes if len(c) == 6 and c.isdigit()]
                    self.logger.info(f"daily({trade_date}) 获取 {len(codes)} 个股票代码")
                    return codes
            except Exception as e:
                self.logger.warning(f"daily({trade_date}) 失败: {e}")
        self.logger.error("获取股票代码失败")
        return []

    # ------------------------------------------------------------------
    # 日线数据（前复权 + 内存/磁盘双缓存）
    # ------------------------------------------------------------------
    def get_stock_daily(self, code, days=120):
        """获取股票日线数据（带重试 + 内存/磁盘双缓存）"""
        # 1. 内存缓存
        if code in self._daily_cache:
            self.logger.debug(f"{code} 日线命中内存缓存")
            return self._daily_cache[code]

        # 2. 磁盘缓存
        cached = self._load_cache(code)
        if cached is not None:
            self._daily_cache[code] = cached
            return cached

        start    = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        end      = datetime.now().strftime('%Y%m%d')
        ts_code  = _to_ts_code(code)

        for attempt in range(MAX_RETRIES):
            try:
                self.logger.debug(f"{code} 日线 尝试{attempt+1}")
                df = ts.pro_bar(
                    ts_code=ts_code, adj='qfq',
                    start_date=start, end_date=end,
                    freq='D'
                )
                if df is not None and not df.empty:
                    result = self._normalize_tushare(df, code)
                    self._daily_cache[code] = result
                    self._save_cache(code, result)
                    return result
                self.logger.warning(f"{code} 日线返回空数据")
                break
            except Exception as e:
                self.logger.warning(f"{code} 日线 尝试{attempt+1} 失败: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        self.logger.error(f"{code} 日线获取失败")
        return None

    # ------------------------------------------------------------------
    # 周线数据（由日线 resample 生成）
    # ------------------------------------------------------------------
    def get_stock_weekly(self, code, weeks=52):
        """获取股票周线数据（由日线聚合）"""
        return self._weekly_from_daily(code, weeks)

    def _weekly_from_daily(self, code, weeks=52):
        """由日线数据 resample 生成周线"""
        if code in self._daily_cache:
            daily = self._daily_cache[code]
        else:
            daily = self.get_stock_daily(code, days=weeks * 7 + 30)
        if daily is None or daily.empty:
            return None
        df = daily.copy().set_index('日期')

        agg_dict = {
            '开盘价': 'first',
            '收盘价': 'last',
            '最高价': 'max',
            '最低价': 'min',
            '成交量': 'sum',
        }
        if '成交额' in df.columns:
            agg_dict['成交额'] = 'sum'

        weekly = df.resample('W').agg(agg_dict).dropna(subset=['收盘价'])
        weekly = weekly.reset_index()

        for col in ['成交额', '振幅', '涨跌幅', '涨跌额', '换手率']:
            if col not in weekly.columns:
                weekly[col] = 0.0

        weekly = weekly[['日期', '开盘价', '收盘价', '最高价', '最低价',
                          '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']]
        weekly['代码'] = code
        self.logger.debug(f"{code} 日线聚合周线 {len(weekly)} 条")
        return weekly

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    def _normalize_tushare(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """将 Tushare 返回的列名映射为系统统一格式"""
        col_map = {
            'trade_date': '日期',
            'open':       '开盘价',
            'close':      '收盘价',
            'high':       '最高价',
            'low':        '最低价',
            'vol':        '成交量',
            'amount':     '成交额',
            'pct_chg':    '涨跌幅',
            'change':     '涨跌额',
            'turnover_rate': '换手率',
        }
        df = df.rename(columns=col_map)
        df['日期'] = pd.to_datetime(df['日期'])
        for col in ['开盘价', '收盘价', '最高价', '最低价']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if '成交量' in df.columns:
            df['成交量'] = pd.to_numeric(df['成交量'], errors='coerce').fillna(0).astype(float)
        if '振幅' not in df.columns:
            df['振幅'] = 0.0
        if '换手率' not in df.columns:
            df['换手率'] = 0.0
        df = df.sort_values('日期').reset_index(drop=True)
        df['代码'] = code
        keep = ['日期', '开盘价', '收盘价', '最高价', '最低价',
                '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率', '代码']
        for c in keep:
            if c not in df.columns:
                df[c] = 0.0
        return df[keep]

    def get_stock_info(self, code):
        try:
            df = self.get_stock_daily(code, days=5)
            if df is not None and not df.empty:
                return df.iloc[-1]
            return None
        except Exception as e:
            self.logger.error(f"获取 {code} 基本信息失败: {e}")
            return None


def fetch_data(code):
    """便捷函数：获取某个股票的日线和周线数据"""
    fetcher = DataFetcher()
    return fetcher.get_stock_daily(code, days=120), fetcher.get_stock_weekly(code, weeks=52)
