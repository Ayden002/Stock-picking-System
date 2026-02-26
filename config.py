"""
配置文件
"""
import os
from datetime import datetime, timedelta

# 项目根路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据存储路径
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 选股条件配置
STOCK_FILTER_CONFIG = {
    # 周线金叉：MA5 > MA10
    'ma5_period': 5,
    'ma10_period': 10,
    
    # 十五个交易日内有过涨停
    'limit_up_days': 15,
    
    # 五个交易日内有倍量交易（成交量是前20日平均的2倍以上）
    'volume_multiple_days': 5,
    'volume_multiple_ratio': 2.0,
    'volume_avg_period': 20,
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': os.path.join(LOG_DIR, f'stock_selector_{datetime.now().strftime("%Y%m%d")}.log'),
}

# 涨停判断（收盘价相对前日涨幅）
LIMIT_UP_THRESHOLD = 0.095  # 9.5%，用于非ST股票

# 数据更新间隔（秒）
DATA_UPDATE_INTERVAL = 3600  # 1小时更新一次数据

# 要检查的股票列表（为空表示检查全部A股）
# STOCK_LIST = ['000001', '000002']  # 可以指定特定股票
STOCK_LIST = []

# 超时配置（秒）
REQUEST_TIMEOUT = 60

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒（每次重试延迟会递增：2s, 4s, 6s）
