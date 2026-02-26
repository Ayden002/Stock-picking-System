"""
数据获取模块 - 使用 AKshare 接口
"""
import akshare as ak
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta
import time
from logger import get_logger
from config import (
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    LIMIT_UP_THRESHOLD, STOCK_FILTER_CONFIG
)

logger = get_logger(__name__)

# -----------------------------------------------------------------------
# 在 HTTPAdapter.send 层注入 Headers，覆盖 AKshare 所有 Session/Adapter
# -----------------------------------------------------------------------
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://quote.eastmoney.com/",
    "Origin": "https://quote.eastmoney.com",
    "Connection": "keep-alive",
}

_orig_adapter_send = HTTPAdapter.send

# 需要东方财富 Headers 的域名
_EM_DOMAINS = ('eastmoney.com', 'akshare.akfamily.xyz')

def _patched_adapter_send(self, request, **kwargs):
    # 深交所/上交所等官方网站不注入东方财富 Referer
    url = getattr(request, 'url', '') or ''
    need_em = any(d in url for d in _EM_DOMAINS)
    for k, v in _HEADERS.items():
        if k in ('Referer', 'Origin') and not need_em:
            continue
        request.headers.setdefault(k, v)
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    return _orig_adapter_send(self, request, **kwargs)

HTTPAdapter.send = _patched_adapter_send
# -----------------------------------------------------------------------

_DAILY_COLS = ['日期', '开盘价', '收盘价', '最高价', '最低价',
               '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
_WEEKLY_COLS = _DAILY_COLS


def _code_prefix(code: str) -> str:
    """给代码加上交易所前缀（供备用接口使用）"""
    if code.startswith(('0', '3')):
        return 'sz' + code
    elif code.startswith(('6', '9')):
        return 'sh' + code
    elif code.startswith('4') or code.startswith('8'):
        return 'bj' + code
    return code


class DataFetcher:
    """数据获取器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._daily_cache: dict = {}   # {code: DataFrame} 本次运行内缓存

    # ------------------------------------------------------------------
    # 获取股票代码列表（多接口备用）
    # ------------------------------------------------------------------
    def get_all_stock_codes(self):
        """获取所有A股股票代码（依次尝试多个接口）"""
        self.logger.info("开始获取所有A股股票代码...")
        methods = [
            ("stock_info_a_code_name", self._codes_via_info_a_code_name),
            ("stock_zh_a_spot_em",     self._codes_via_spot_em),
            ("stock_sh+sz_a_spot_em",  self._codes_via_sh_sz_list),
        ]
        for name, method in methods:
            try:
                self.logger.info(f"尝试接口: {name}")
                codes = method()
                if codes:
                    codes = [c for c in codes if len(c) == 6 and c.isdigit()]
                    self.logger.info(f"成功获取 {len(codes)} 个股票代码")
                    return codes
            except Exception as e:
                self.logger.warning(f"接口 {name} 失败: {e}")
                time.sleep(RETRY_DELAY)
        self.logger.error("所有获取股票代码的接口均失败")
        return []

    def _codes_via_info_a_code_name(self):
        """直接调用上交所/深交所/北交所子接口拼合，避免 lru_cache 缓存旧失败"""
        codes = []
        # 上交所主板 + 科创板
        for symbol in ['主板A股', '科创板']:
            try:
                df = ak.stock_info_sh_name_code(symbol=symbol)
                col = '证券代码' if '证券代码' in df.columns else df.columns[0]
                codes += df[col].astype(str).str.zfill(6).tolist()
                self.logger.debug(f'上交所[{symbol}] {len(df)} 条')
            except Exception as e:
                self.logger.warning(f'上交所[{symbol}] 失败: {e}')
        # 深交所
        try:
            df = ak.stock_info_sz_name_code(symbol='A股列表')
            col = 'A股代码' if 'A股代码' in df.columns else df.columns[0]
            codes += df[col].astype(str).str.zfill(6).tolist()
            self.logger.debug(f'深交所 {len(df)} 条')
        except Exception as e:
            self.logger.warning(f'深交所失败: {e}')
        # 北交所
        try:
            df = ak.stock_info_bj_name_code()
            col = '证券代码' if '证券代码' in df.columns else df.columns[0]
            codes += df[col].astype(str).str.zfill(6).tolist()
            self.logger.debug(f'北交所 {len(df)} 条')
        except Exception as e:
            self.logger.warning(f'北交所失败: {e}')
        return codes

    def _codes_via_spot_em(self):
        df = ak.stock_zh_a_spot_em()
        return df['代码'].tolist()

    def _codes_via_sh_sz_list(self):
        codes = []
        for fn in [ak.stock_sh_a_spot_em, ak.stock_sz_a_spot_em]:
            try:
                df = fn()
                codes += df['代码'].tolist()
            except Exception as e:
                self.logger.warning(f"子接口失败: {e}")
        return codes

    # ------------------------------------------------------------------
    # 日线数据（多数据源备用）
    # ------------------------------------------------------------------
    def get_stock_daily(self, code, days=120):
        """获取股票日线数据（带重试 + 多数据源 + 本地缓存）"""
        # 命中缓存则直接返回（避免同一 code 重复请求）
        if code in self._daily_cache:
            self.logger.debug(f"{code} 日线命中缓存")
            return self._daily_cache[code]

        start = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        end   = datetime.now().strftime('%Y%m%d')

        # 数据源：东方财富历史行情 → 新浪财经
        sources = [
            ("东方财富", lambda: ak.stock_zh_a_hist(
                symbol=code, period='daily',
                start_date=start, end_date=end, adjust='qfq'
            )),
            ("新浪", lambda: ak.stock_zh_a_daily(
                symbol=_code_prefix(code),
                start_date=start, end_date=end, adjust='qfq'
            )),
        ]

        for src_name, source_fn in sources:
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.debug(f"{code} 日线[{src_name}] 尝试{attempt+1}")
                    df = source_fn()
                    if df is not None and not df.empty:
                        result = self._normalize(df, _DAILY_COLS, code)
                        self._daily_cache[code] = result   # 写入缓存
                        return result
                    self.logger.warning(f"{code} 日线[{src_name}] 返回空数据")
                    break
                except Exception as e:
                    self.logger.warning(f"{code} 日线[{src_name}] 尝试{attempt+1} 失败: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
            self.logger.info(f"{code} 日线[{src_name}] 失败，尝试下一数据源")

        self.logger.error(f"{code} 日线所有数据源均失败")
        return None

    # ------------------------------------------------------------------
    # 周线数据（直接获取失败则由日线聚合）
    # ------------------------------------------------------------------
    def get_stock_weekly(self, code, weeks=52):
        """获取股票周线数据：先直接获取，失败则由日线聚合"""
        start = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y%m%d')
        end   = datetime.now().strftime('%Y%m%d')

        # 先尝试直接拉取周线
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.debug(f"{code} 周线直接获取 尝试{attempt+1}")
                df = ak.stock_zh_a_hist(
                    symbol=code, period='weekly',
                    start_date=start, end_date=end, adjust='qfq'
                )
                if df is not None and not df.empty:
                    return self._normalize(df, _WEEKLY_COLS, code)
            except Exception as e:
                self.logger.warning(f"{code} 周线直接获取 尝试{attempt+1} 失败: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        # 备用：由日线聚合周线
        self.logger.info(f"{code} 周线直接获取失败，改用日线聚合")
        return self._weekly_from_daily(code, weeks)

    def _weekly_from_daily(self, code, weeks=52):
        """由日线数据 resample 生成周线（优先使用已缓存的日线）"""
        # 优先用缓存，避免重复请求新浪被限速
        if code in self._daily_cache:
            daily = self._daily_cache[code]
        else:
            daily = self.get_stock_daily(code, days=weeks * 7 + 30)
        if daily is None or daily.empty:
            return None
        df = daily.copy()
        df = df.set_index('日期')

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
    def _normalize(self, df: pd.DataFrame, cols, code: str) -> pd.DataFrame:
        """统一列名、数值类型、排序"""
        df = df.iloc[:, :len(cols)].copy()
        df.columns = cols[:len(df.columns)]
        df['日期'] = pd.to_datetime(df['日期'])
        for c in ['开盘价', '收盘价', '最高价', '最低价']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        if '成交量' in df.columns:
            df['成交量'] = pd.to_numeric(df['成交量'], errors='coerce').fillna(0).astype(float)
        df = df.sort_values('日期').reset_index(drop=True)
        df['代码'] = code
        return df

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
