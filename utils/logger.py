"""
日誌系統模組 - 配置日誌記錄
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from config import LOG_FILE, LOG_LEVEL


def setup_logger():
    """設定日誌系統"""
    # 確保日誌目錄存在
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 設定日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 主 logger
    logger = logging.getLogger('discord')
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # 檔案處理器（最大 5MB，保留 5 個備份）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    return logger
