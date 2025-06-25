"""
Logger Module for CloudWatch Logs Analyzer

This module provides logging functionality for the application.
"""

import logging
import os
import sys
from typing import Optional

def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and log level.
    
    Args:
        name (str): Name of the logger
        log_level (int, optional): Log level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Create file handler if log directory exists
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if os.path.exists(log_dir):
        log_file = os.path.join(log_dir, f'{name}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with the specified name and log level.
    
    Args:
        name (str): Name of the logger
        log_level (int, optional): Log level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Configured logger
    """
    return setup_logger(name, log_level)

# Create application logger
app_logger = setup_logger('cloudwatch_logs_analyzer')
