"""
File operations utilities for reading, writing, and managing files.

This module provides utilities for common file operations with proper
error handling and encoding support.
"""

from pathlib import Path
from typing import Union, List, Optional
import glob as glob_module
from ..logging.logger import get_logger
from ..errors.exceptions import SiteGenError

logger = get_logger(__name__)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
        
    Raises:
        SiteGenError: If directory creation fails
        
    Example:
        >>> dir_path = ensure_dir('output/data')
        >>> print(dir_path.exists())
        True
    """
    try:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
        return path
    except Exception as e:
        error_msg = f"Failed to create directory {path}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e


def read_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read text file content.
    
    Args:
        path: File path
        encoding: Text encoding (default: utf-8)
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        SiteGenError: If read fails
        
    Example:
        >>> content = read_text('data/config.txt')
    """
    try:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = path.read_text(encoding=encoding)
        logger.debug(f"Read {len(content)} characters from {path}")
        return content
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Failed to read {path}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e


def write_text(
    path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    ensure_parent: bool = True
) -> None:
    """
    Write text content to file.
    
    Args:
        path: File path
        content: Text content to write
        encoding: Text encoding (default: utf-8)
        ensure_parent: Create parent directories if needed
        
    Raises:
        SiteGenError: If write fails
        
    Example:
        >>> write_text('output/result.txt', 'Hello World')
    """
    try:
        path = Path(path)
        
        if ensure_parent:
            ensure_dir(path.parent)
        
        path.write_text(content, encoding=encoding)
        logger.debug(f"Wrote {len(content)} characters to {path}")
    except Exception as e:
        error_msg = f"Failed to write to {path}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e


def list_files(
    directory: Union[str, Path],
    pattern: str = '*',
    recursive: bool = False
) -> List[Path]:
    """
    List files in directory matching pattern.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (default: *)
        recursive: Search recursively
        
    Returns:
        List of Path objects
        
    Example:
        >>> files = list_files('data', '*.txt')
        >>> md_files = list_files('docs', '*.md', recursive=True)
    """
    try:
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []
        
        if recursive:
            pattern_path = f"**/{pattern}"
            files = list(directory.glob(pattern_path))
        else:
            files = list(directory.glob(pattern))
        
        # Filter to only files (not directories)
        files = [f for f in files if f.is_file()]
        
        logger.debug(f"Found {len(files)} files in {directory} matching {pattern}")
        return files
    except Exception as e:
        error_msg = f"Failed to list files in {directory}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e


def read_lines(
    path: Union[str, Path],
    encoding: str = 'utf-8',
    strip: bool = True
) -> List[str]:
    """
    Read file lines into a list.
    
    Args:
        path: File path
        encoding: Text encoding
        strip: Strip whitespace from each line
        
    Returns:
        List of lines
        
    Example:
        >>> lines = read_lines('data.txt')
    """
    content = read_text(path, encoding)
    lines = content.splitlines()
    
    if strip:
        lines = [line.strip() for line in lines]
    
    return lines


def write_lines(
    path: Union[str, Path],
    lines: List[str],
    encoding: str = 'utf-8',
    ensure_parent: bool = True
) -> None:
    """
    Write list of lines to file.
    
    Args:
        path: File path
        lines: List of lines
        encoding: Text encoding
        ensure_parent: Create parent directories
        
    Example:
        >>> write_lines('output.txt', ['Line 1', 'Line 2'])
    """
    content = '\n'.join(lines)
    write_text(path, content, encoding, ensure_parent)


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if file exists.
    
    Args:
        path: File path
        
    Returns:
        True if file exists
        
    Example:
        >>> if file_exists('config.yaml'):
        ...     print('Config found')
    """
    return Path(path).is_file()


def dir_exists(path: Union[str, Path]) -> bool:
    """
    Check if directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        True if directory exists
        
    Example:
        >>> if dir_exists('data'):
        ...     print('Data directory exists')
    """
    return Path(path).is_dir()


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        path: File path
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
        
    Example:
        >>> size = get_file_size('data.txt')
        >>> print(f'File is {size} bytes')
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    return path.stat().st_size


def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    ensure_parent: bool = True
) -> None:
    """
    Copy file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        ensure_parent: Create parent directories
        
    Raises:
        FileNotFoundError: If source doesn't exist
        SiteGenError: If copy fails
        
    Example:
        >>> copy_file('template.txt', 'output/final.txt')
    """
    try:
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if ensure_parent:
            ensure_dir(destination.parent)
        
        import shutil
        shutil.copy2(source, destination)
        logger.debug(f"Copied {source} to {destination}")
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Failed to copy {source} to {destination}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e


def delete_file(path: Union[str, Path]) -> None:
    """
    Delete a file.
    
    Args:
        path: File path
        
    Raises:
        FileNotFoundError: If file doesn't exist
        SiteGenError: If deletion fails
        
    Example:
        >>> delete_file('temp.txt')
    """
    try:
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        path.unlink()
        logger.debug(f"Deleted file: {path}")
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Failed to delete {path}: {str(e)}"
        logger.error(error_msg)
        raise SiteGenError(error_msg) from e
