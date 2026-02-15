"""
Unit tests for file operations.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from lib.io.file_ops import (
    ensure_dir,
    read_text,
    write_text,
    list_files,
    read_lines,
    write_lines,
    file_exists,
    dir_exists,
    get_file_size,
    copy_file,
    delete_file
)
from lib.errors.exceptions import SiteGenError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.mark.unit
def test_ensure_dir_creates_directory(temp_dir):
    """Test that ensure_dir creates a new directory."""
    new_dir = temp_dir / 'test_dir'
    result = ensure_dir(new_dir)
    
    assert result.exists()
    assert result.is_dir()
    assert result == new_dir


@pytest.mark.unit
def test_ensure_dir_creates_nested_directories(temp_dir):
    """Test that ensure_dir creates nested directories."""
    nested_dir = temp_dir / 'level1' / 'level2' / 'level3'
    result = ensure_dir(nested_dir)
    
    assert result.exists()
    assert result.is_dir()


@pytest.mark.unit
def test_ensure_dir_with_existing_directory(temp_dir):
    """Test that ensure_dir works with existing directories."""
    # Create directory first
    test_dir = temp_dir / 'existing'
    test_dir.mkdir()
    
    # Should not raise error
    result = ensure_dir(test_dir)
    assert result.exists()


@pytest.mark.unit
def test_write_and_read_text(temp_dir):
    """Test file write and read cycle."""
    test_file = temp_dir / 'test.txt'
    test_content = 'Hello, World!'
    
    write_text(test_file, test_content)
    read_content = read_text(test_file)
    
    assert read_content == test_content
    assert test_file.exists()


@pytest.mark.unit
def test_write_text_creates_parent_dirs(temp_dir):
    """Test that write_text creates parent directories."""
    test_file = temp_dir / 'nested' / 'dir' / 'test.txt'
    content = 'Test content'
    
    write_text(test_file, content)
    
    assert test_file.exists()
    assert read_text(test_file) == content


@pytest.mark.unit
def test_write_text_without_ensure_parent(temp_dir):
    """Test writing to file when parent doesn't exist and ensure_parent=False."""
    test_dir = temp_dir / 'parent'
    test_dir.mkdir()
    test_file = test_dir / 'test.txt'
    
    # Should work because parent exists
    write_text(test_file, 'content', ensure_parent=False)
    assert test_file.exists()


@pytest.mark.unit
def test_list_files_glob(temp_dir):
    """Test glob pattern matching for listing files."""
    # Create test files
    (temp_dir / 'file1.txt').write_text('content1')
    (temp_dir / 'file2.txt').write_text('content2')
    (temp_dir / 'file3.md').write_text('content3')
    (temp_dir / 'subdir').mkdir()
    (temp_dir / 'subdir' / 'file4.txt').write_text('content4')
    
    # Test pattern matching
    txt_files = list_files(temp_dir, '*.txt')
    
    assert len(txt_files) == 2
    assert all(f.suffix == '.txt' for f in txt_files)
    
    # Test all files
    all_files = list_files(temp_dir, '*')
    assert len(all_files) == 3  # Should not include subdirectory


@pytest.mark.unit
def test_list_files_recursive(temp_dir):
    """Test recursive file listing."""
    # Create nested structure
    (temp_dir / 'file1.txt').write_text('content')
    subdir = temp_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'file2.txt').write_text('content')
    
    # Non-recursive
    files = list_files(temp_dir, '*.txt', recursive=False)
    assert len(files) == 1
    
    # Recursive
    files_recursive = list_files(temp_dir, '*.txt', recursive=True)
    assert len(files_recursive) == 2


@pytest.mark.unit
def test_list_files_nonexistent_directory(temp_dir):
    """Test listing files in non-existent directory."""
    non_existent = temp_dir / 'does_not_exist'
    files = list_files(non_existent, '*.txt')
    
    assert files == []


@pytest.mark.unit
def test_utf8_encoding(temp_dir):
    """Test UTF-8 handling with special characters."""
    test_file = temp_dir / 'unicode.txt'
    content = 'Hello 世界! Привет мир! 🚀 Émojis & spëcial çhars'
    
    write_text(test_file, content, encoding='utf-8')
    read_content = read_text(test_file, encoding='utf-8')
    
    assert read_content == content


@pytest.mark.unit
def test_read_nonexistent_file(temp_dir):
    """Test error handling for missing files."""
    non_existent = temp_dir / 'does_not_exist.txt'
    
    with pytest.raises(FileNotFoundError):
        read_text(non_existent)


@pytest.mark.unit
def test_read_lines(temp_dir):
    """Test reading file as lines."""
    test_file = temp_dir / 'lines.txt'
    content = 'Line 1\nLine 2\nLine 3'
    write_text(test_file, content)
    
    lines = read_lines(test_file)
    
    assert len(lines) == 3
    assert lines[0] == 'Line 1'
    assert lines[2] == 'Line 3'


@pytest.mark.unit
def test_read_lines_with_whitespace(temp_dir):
    """Test reading lines with whitespace handling."""
    test_file = temp_dir / 'lines.txt'
    content = '  Line 1  \n  Line 2  \n  Line 3  '
    write_text(test_file, content)
    
    # With strip=True (default)
    lines = read_lines(test_file, strip=True)
    assert lines[0] == 'Line 1'
    
    # With strip=False
    lines_no_strip = read_lines(test_file, strip=False)
    assert lines_no_strip[0] == '  Line 1  '


@pytest.mark.unit
def test_write_lines(temp_dir):
    """Test writing list of lines."""
    test_file = temp_dir / 'lines.txt'
    lines = ['First line', 'Second line', 'Third line']
    
    write_lines(test_file, lines)
    
    content = read_text(test_file)
    assert 'First line' in content
    assert 'Second line' in content
    assert content.count('\n') == 2


@pytest.mark.unit
def test_file_exists(temp_dir):
    """Test file existence check."""
    test_file = temp_dir / 'test.txt'
    
    assert not file_exists(test_file)
    
    write_text(test_file, 'content')
    
    assert file_exists(test_file)


@pytest.mark.unit
def test_dir_exists(temp_dir):
    """Test directory existence check."""
    test_dir = temp_dir / 'testdir'
    
    assert not dir_exists(test_dir)
    
    ensure_dir(test_dir)
    
    assert dir_exists(test_dir)


@pytest.mark.unit
def test_get_file_size(temp_dir):
    """Test getting file size."""
    test_file = temp_dir / 'size_test.txt'
    content = 'Hello World'
    write_text(test_file, content)
    
    size = get_file_size(test_file)
    
    assert size == len(content.encode('utf-8'))


@pytest.mark.unit
def test_get_file_size_nonexistent(temp_dir):
    """Test get_file_size with non-existent file."""
    non_existent = temp_dir / 'missing.txt'
    
    with pytest.raises(FileNotFoundError):
        get_file_size(non_existent)


@pytest.mark.unit
def test_copy_file(temp_dir):
    """Test file copying."""
    source = temp_dir / 'source.txt'
    destination = temp_dir / 'dest.txt'
    content = 'Copy me!'
    
    write_text(source, content)
    copy_file(source, destination)
    
    assert destination.exists()
    assert read_text(destination) == content


@pytest.mark.unit
def test_copy_file_with_nested_destination(temp_dir):
    """Test copying to nested destination."""
    source = temp_dir / 'source.txt'
    destination = temp_dir / 'nested' / 'dir' / 'dest.txt'
    content = 'Copy me!'
    
    write_text(source, content)
    copy_file(source, destination)
    
    assert destination.exists()
    assert read_text(destination) == content


@pytest.mark.unit
def test_copy_file_nonexistent_source(temp_dir):
    """Test copying non-existent file."""
    source = temp_dir / 'missing.txt'
    destination = temp_dir / 'dest.txt'
    
    with pytest.raises(FileNotFoundError):
        copy_file(source, destination)


@pytest.mark.unit
def test_delete_file(temp_dir):
    """Test file deletion."""
    test_file = temp_dir / 'delete_me.txt'
    write_text(test_file, 'content')
    
    assert test_file.exists()
    
    delete_file(test_file)
    
    assert not test_file.exists()


@pytest.mark.unit
def test_delete_nonexistent_file(temp_dir):
    """Test deleting non-existent file."""
    non_existent = temp_dir / 'missing.txt'
    
    with pytest.raises(FileNotFoundError):
        delete_file(non_existent)


@pytest.mark.unit
def test_path_types(temp_dir):
    """Test that functions work with both str and Path types."""
    test_file_str = str(temp_dir / 'test.txt')
    test_file_path = temp_dir / 'test2.txt'
    content = 'Test content'
    
    # Test with string
    write_text(test_file_str, content)
    assert read_text(test_file_str) == content
    
    # Test with Path
    write_text(test_file_path, content)
    assert read_text(test_file_path) == content


@pytest.mark.unit
def test_empty_file(temp_dir):
    """Test handling of empty files."""
    test_file = temp_dir / 'empty.txt'
    write_text(test_file, '')
    
    content = read_text(test_file)
    assert content == ''
    
    lines = read_lines(test_file)
    assert lines == []  # Empty file has no lines
