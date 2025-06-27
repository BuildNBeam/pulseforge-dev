import logging
import os
from datetime import datetime
from config import Config

def setup_logger(name):
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler(f'logs/{Config.LOG_FILE}')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
