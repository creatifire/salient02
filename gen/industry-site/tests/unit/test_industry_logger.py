"""
Unit tests for industry-specific file logging.
"""

import pytest
import logging
from pathlib import Path
from datetime import datetime
from lib.logging.logger import setup_industry_logger, get_log_file_path, get_logger


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    return tmp_path / "test_logs"


@pytest.mark.unit
def test_creates_log_directory(temp_log_dir):
    """Test that setup_industry_logger creates the logs directory."""
    # Initially directory should not exist
    assert not temp_log_dir.exists()
    
    # Setup logger
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    
    # Verify directory was created
    assert temp_log_dir.exists()
    assert temp_log_dir.is_dir()


@pytest.mark.unit
def test_log_file_naming(temp_log_dir):
    """Test that log filename matches expected pattern."""
    logger = setup_industry_logger('agtech', '01_init_config', log_dir=temp_log_dir)
    
    # Get list of files in log directory
    log_files = list(temp_log_dir.glob('*.log'))
    
    # Should have exactly one log file
    assert len(log_files) == 1
    
    log_file = log_files[0]
    filename = log_file.name
    
    # Verify filename pattern: <industry>_<script>_<timestamp>.log
    assert filename.startswith('agtech_01_init_config_')
    assert filename.endswith('.log')
    
    # Extract and verify timestamp format (YYYYMMDD_HHMMSS)
    parts = filename.replace('.log', '').split('_')
    assert len(parts) >= 4  # industry, script_num, date, time
    
    date_part = parts[-2]  # YYYYMMDD
    time_part = parts[-1]  # HHMMSS
    
    assert len(date_part) == 8  # YYYYMMDD
    assert date_part.isdigit()
    assert len(time_part) == 6  # HHMMSS
    assert time_part.isdigit()


@pytest.mark.unit
def test_dual_output(temp_log_dir):
    """Test that logs appear in both console and file."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    
    test_message = "Test message for dual output"
    
    # Log at INFO level
    logger.info(test_message)
    
    # Verify file output
    log_files = list(temp_log_dir.glob('*.log'))
    assert len(log_files) == 1
    
    log_content = log_files[0].read_text()
    assert test_message in log_content
    
    # Verify logger has both file and console handlers
    assert len(logger.handlers) == 2
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert 'StreamHandler' in handler_types  # Console
    assert 'FileHandler' in handler_types     # File


@pytest.mark.unit
def test_multiple_loggers(temp_log_dir):
    """Test that multiple script loggers work independently."""
    # Create loggers for different scripts
    logger1 = setup_industry_logger('agtech', '01_init', log_dir=temp_log_dir)
    logger2 = setup_industry_logger('agtech', '02_research', log_dir=temp_log_dir)
    
    # Log different messages
    logger1.info('Message from script 01')
    logger2.info('Message from script 02')
    
    # Should have two separate log files
    log_files = sorted(temp_log_dir.glob('*.log'))
    assert len(log_files) == 2
    
    # Verify file names
    assert 'agtech_01_init' in log_files[0].name
    assert 'agtech_02_research' in log_files[1].name
    
    # Verify messages went to correct files
    log1_content = log_files[0].read_text()
    log2_content = log_files[1].read_text()
    
    assert 'Message from script 01' in log1_content
    assert 'Message from script 01' not in log2_content
    
    assert 'Message from script 02' in log2_content
    assert 'Message from script 02' not in log1_content


@pytest.mark.unit
def test_log_levels(temp_log_dir):
    """Test that different log levels work correctly."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    
    # Log at different levels
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    logger.critical('Critical message')
    
    # Read log file
    log_files = list(temp_log_dir.glob('*.log'))
    log_content = log_files[0].read_text()
    
    # All levels should be in file (file_level=DEBUG)
    assert 'DEBUG' in log_content
    assert 'Debug message' in log_content
    assert 'INFO' in log_content
    assert 'Info message' in log_content
    assert 'WARNING' in log_content
    assert 'Warning message' in log_content
    assert 'ERROR' in log_content
    assert 'Error message' in log_content
    assert 'CRITICAL' in log_content
    assert 'Critical message' in log_content


@pytest.mark.unit
def test_log_format_includes_function_and_line(temp_log_dir):
    """Test that file logs include function name and line number."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    logger.info('Test message')
    
    log_files = list(temp_log_dir.glob('*.log'))
    log_content = log_files[0].read_text()
    
    # Verify format includes function name and line number
    # Format: %(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
    assert ' - test_log_format_includes_function_and_line:' in log_content or ' - <module>:' in log_content
    assert ' - Test message' in log_content


@pytest.mark.unit
def test_log_timestamps(temp_log_dir):
    """Test that log entries have timestamps."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    logger.info('Timestamped message')
    
    log_files = list(temp_log_dir.glob('*.log'))
    log_content = log_files[0].read_text()
    
    # Verify timestamp format at start of line (YYYY-MM-DD HH:MM:SS)
    # Should match pattern like: 2026-02-13 23:07:47
    import re
    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    assert re.search(timestamp_pattern, log_content)


@pytest.mark.unit
def test_get_log_file_path():
    """Test get_log_file_path utility function."""
    # Test with default timestamp
    path = get_log_file_path('agtech', '01_init')
    
    assert isinstance(path, Path)
    assert 'agtech' in str(path)
    assert 'logs' in str(path)
    assert path.name.startswith('agtech_01_init_')
    assert path.name.endswith('.log')
    
    # Test with explicit timestamp
    path = get_log_file_path('agtech', '02_research', timestamp='20260213_150000')
    assert path.name == 'agtech_02_research_20260213_150000.log'


@pytest.mark.unit
def test_logger_initialization_message(temp_log_dir):
    """Test that logger logs its own initialization."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    
    log_files = list(temp_log_dir.glob('*.log'))
    log_content = log_files[0].read_text()
    
    # Should have initialization messages
    assert 'Logging initialized:' in log_content
    assert 'Log file path:' in log_content


@pytest.mark.unit
def test_get_logger_basic():
    """Test that get_logger returns a logger instance."""
    logger = get_logger(__name__)
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == __name__


@pytest.mark.unit
def test_different_industries(temp_log_dir):
    """Test logging for different industries."""
    logger1 = setup_industry_logger('agtech', 'script', log_dir=temp_log_dir)
    logger2 = setup_industry_logger('healthtech', 'script', log_dir=temp_log_dir)
    
    logger1.info('AgTech message')
    logger2.info('HealthTech message')
    
    log_files = sorted(temp_log_dir.glob('*.log'))
    assert len(log_files) == 2
    
    # Verify separate files for different industries
    filenames = [f.name for f in log_files]
    assert any('agtech' in name for name in filenames)
    assert any('healthtech' in name for name in filenames)


@pytest.mark.unit
def test_unicode_messages(temp_log_dir):
    """Test that unicode characters are handled correctly."""
    logger = setup_industry_logger('test_industry', 'test_script', log_dir=temp_log_dir)
    
    unicode_message = "测试消息 émojis 🚀 symbols ±≈"
    logger.info(unicode_message)
    
    log_files = list(temp_log_dir.glob('*.log'))
    log_content = log_files[0].read_text(encoding='utf-8')
    
    assert unicode_message in log_content
