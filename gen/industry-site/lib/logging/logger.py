"""
Logging integration for Industry Site Generator.
Console and file-based logging without external dependencies.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get standard Python logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Standard Python logger instance
    """
    return logging.getLogger(name)


def setup_industry_logger(
    industry: str,
    script_name: str,
    log_dir: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Setup dual logger (console + file) for industry site generation.
    
    Creates timestamped log file in industry-specific logs directory.
    Configures both console and file handlers with appropriate formatting.
    
    Args:
        industry: Industry name (e.g., 'agtech')
        script_name: Script identifier (e.g., '01_init_config' or 'full')
        log_dir: Optional custom log directory (defaults to <industry>/logs/)
        console_level: Console logging level (default: INFO)
        file_level: File logging level (default: DEBUG)
        
    Returns:
        Configured logger instance with dual output
        
    Example:
        logger = setup_industry_logger('agtech', '01_init_config')
        logger.info('Starting config initialization')
        logger.debug('Loading config from file')
    """
    # Determine log directory
    if log_dir is None:
        # Default: gen/industry-site/<industry>/logs/
        log_dir = Path(__file__).parent.parent.parent / industry / 'logs'
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filename: <industry>_<script_num>_<timestamp>.log
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{industry}_{script_name}_{timestamp}.log"
    
    # Create logger with unique name
    logger_name = f"sitegen.{industry}.{script_name}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG and above)
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Log initialization message
    logger.info(f"Logging initialized: {log_file.name}")
    logger.debug(f"Log file path: {log_file.absolute()}")
    
    return logger


def get_log_file_path(
    industry: str,
    script_name: str,
    timestamp: Optional[str] = None
) -> Path:
    """
    Get the path for a log file (without creating it).
    
    Args:
        industry: Industry name
        script_name: Script identifier
        timestamp: Optional timestamp string (default: current time)
        
    Returns:
        Path to log file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    log_dir = Path(__file__).parent.parent.parent / industry / 'logs'
    return log_dir / f"{industry}_{script_name}_{timestamp}.log"

