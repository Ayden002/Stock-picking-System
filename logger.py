"""
日志模块
"""
import logging
import os
from config import LOG_CONFIG

def get_logger(name):
    """获取日志记录器"""
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # 创建文件处理器
    os.makedirs(os.path.dirname(LOG_CONFIG['filename']), exist_ok=True)
    file_handler = logging.FileHandler(LOG_CONFIG['filename'], encoding='utf-8')
    file_handler.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_CONFIG['format'])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
