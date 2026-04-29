"""
配置文件 - 量化选股框架的统一参数中心

所有模块（数据层、规则层、选股、回测、组合管理）都从这里读取参数，
避免阈值/窗口散落在各个文件里。

修改任何参数后重新运行即可生效，无需改动业务代码。
"""
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_DIR   = os.path.join(PROJECT_ROOT, 'data')
CACHE_DIR  = os.path.join(PROJECT_ROOT, 'data', 'cache')   # 本地行情缓存
LOG_DIR    = os.path.join(PROJECT_ROOT, 'logs')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data')             # 选股/回测结果输出

for _d in (DATA_DIR, CACHE_DIR, LOG_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': os.path.join(LOG_DIR, f'quant_{datetime.now().strftime("%Y%m%d")}.log'),
}

# ---------------------------------------------------------------------------
# 数据层
# ---------------------------------------------------------------------------
TUSHARE_TOKEN   = "35d3e168e6c39d292a8e85f7407714f7f788297374ea467349f7cddf"

REQUEST_TIMEOUT = 60          # 单次 HTTP 请求超时（秒）
MAX_RETRIES     = 3           # 接口失败最大重试次数
RETRY_DELAY     = 2           # 重试基础延迟（秒；实际为 delay * attempt）

# 本地缓存：CSV 文件按股票代码存储，超过此天数则视为过期并重新拉取
CACHE_EXPIRE_DAYS = 1         # 缓存有效期（自然日）

# ---------------------------------------------------------------------------
# 选股过滤参数（对应各规则的默认值）
# 注意：这里是"全局默认"，直接传给规则类；若想单独调整某条规则，
#       可在 RULES_CONFIG 里覆盖（见下方）。
# ---------------------------------------------------------------------------
STOCK_FILTER_CONFIG = {
    # ── 金叉规则 ──────────────────────────────────────────────────────────
    'ma5_period'  : 5,          # 短期均线周期
    'ma10_period' : 10,         # 长期均线周期
    'use_weekly'  : True,       # True=周线金叉；False=日线金叉
    'lookback_weeks': 2,        # 最近 N 根K线内发生过真金叉即通过
    'require_ma_long_up': False, # 是否要求长期均线方向向上

    # ── 涨停规则 ──────────────────────────────────────────────────────────
    'limit_up_days'     : 15,   # 向前检查的交易日数
    'limit_up_threshold': 0.095,# 涨停判定阈值（9.5%）

    # ── 倍量规则 ──────────────────────────────────────────────────────────
    'volume_multiple_days'  : 5,   # 向前检查的交易日数
    'volume_multiple_ratio' : 2.0, # 倍量倍数（2 倍均量）
    'volume_avg_period'     : 20,  # 基准均量的计算窗口
    # ── 主力资金规则 (MainFlowRule) ─────────────────────────────
    'mf_flow_out_veto_wan' : 5000.0,  # 5日累计净流出超过此值（万元）一票否决
    'mf_follow_veto'       : -0.3,    # 涪停后主力跟进度 < 此值 即否决
    'mf_min_continuity'    : 0.4,     # 10日净流入天数比例下限
    'mf_net_in_pass_wan'   : 2000.0,  # 5日主力净流入 >= 此值（万元）则强通过
    'mf_require_net_in'    : False,   # 是否强要求 5日 主力净额为正

    # ── 超买过滤规则 (RiskFilterRule) ────────────────────────────
    'rf_rsi_period'        : 14,
    'rf_rsi_overbought'    : 80.0,
    'rf_kdj_n'             : 9,
    'rf_kdj_j_overbought'  : 100.0,
    'rf_boll_warn_z'       : 0.8,

    # ── 流动性过滤 (LiquidityRule) ─────────────────────────────
    'liq_avg_period'       : 20,
    'liq_min_amount_wan'   : 5000.0,    # 日均成交额下限（万元）
    'liq_min_turnover_pct' : 0.5,       # 日均换手率下限（%）；None 关闭

    # ── VCP 波动收敛 (VCPRule) ─────────────────────────────────
    'vcp_short_n'          : 10,
    'vcp_long_n'           : 30,
    'vcp_threshold'        : 0.6,
    'vcp_max_drawdown'     : 0.2,
    'vcp_max_dist_to_high' : 0.05,

    # ── 箱体突破 (BoxBreakoutRule) ─────────────────────────────
    'box_window'           : 30,
    'box_lookback_days'    : 3,
    'box_min_break_pct'    : 0.005,
    'box_vol_ratio'        : 1.5,
}

# 涨停阈值（保留此别名以兼容旧代码）
LIMIT_UP_THRESHOLD = STOCK_FILTER_CONFIG['limit_up_threshold']

# 要检查的股票白名单（空列表 = 检查全部 A 股）
STOCK_LIST: list = []

# ---------------------------------------------------------------------------
# 回测参数
# ---------------------------------------------------------------------------
BACKTEST_CONFIG = {
    'hold_days'  : 5,       # 默认持有交易日数（T+1 买入，持有 N 天后卖出）
    'commission' : 0.0003,  # 单边手续费率（万三）
    'slippage'   : 0.001,   # 单边滑点比例
}

# ---------------------------------------------------------------------------
# 组合管理 / 风控参数
# ---------------------------------------------------------------------------
PORTFOLIO_CONFIG = {
    'max_positions'   : 10,        # 最大持仓数量
    'total_capital'   : 100_000.0, # 总资金（元）
    'stop_loss'       : 0.05,      # 止损线（跌幅 5%）
    'take_profit'     : 0.10,      # 止盈线（涨幅 10%）
    'min_position_pct': 0.05,      # 单票最小仓位比例
    'max_position_pct': 0.20,      # 单票最大仓位比例
}

# ---------------------------------------------------------------------------
# 过滤选项（选股前对股票池做预过滤）
# ---------------------------------------------------------------------------
FILTER_OPTIONS = {
    'exclude_st'   : True,   # 过滤 ST / *ST 股票
    'exclude_bj'   : False,  # 是否过滤北交所（4/8 开头）
    'min_list_days': 60,     # 最短上市天数（小于此值不选）
}
