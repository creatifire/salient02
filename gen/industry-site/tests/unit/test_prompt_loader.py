"""
Unit tests for the prompt loader module.
"""

import pytest
from pathlib import Path
from lib.llm.prompts.loader import load_prompt, load_system_prompt, PROMPTS_DIR


@pytest.mark.unit
def test_load_prompt_with_variables(tmp_path):
    """Test loading prompt with variable substitution."""
    # Create a temporary prompt file
    test_category = tmp_path / "test_category"
    test_category.mkdir()
    prompt_file = test_category / "test_prompt.md"
    prompt_file.write_text("Hello {name}! Welcome to {place}.")
    
    # Mock PROMPTS_DIR to use tmp_path
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        result = load_prompt('test_category', 'test_prompt', {
            'name': 'World',
            'place': 'Testing'
        })
        assert result == "Hello World! Welcome to Testing."
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_load_prompt_without_variables(tmp_path):
    """Test loading prompt without variable substitution."""
    test_category = tmp_path / "test_category"
    test_category.mkdir()
    prompt_file = test_category / "simple.md"
    content = "This is a simple prompt with no variables."
    prompt_file.write_text(content)
    
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        result = load_prompt('test_category', 'simple')
        assert result == content
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_missing_prompt_file_raises_error(tmp_path):
    """Test that missing prompt file raises FileNotFoundError."""
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        with pytest.raises(FileNotFoundError) as exc_info:
            load_prompt('nonexistent', 'missing')
        assert "Prompt not found" in str(exc_info.value)
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_missing_variable_raises_error(tmp_path):
    """Test that missing variable in prompt raises KeyError."""
    test_category = tmp_path / "test_category"
    test_category.mkdir()
    prompt_file = test_category / "vars.md"
    prompt_file.write_text("Hello {name}! You are {age} years old.")
    
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        with pytest.raises(KeyError) as exc_info:
            # Only provide 'name', not 'age'
            load_prompt('test_category', 'vars', {'name': 'Alice'})
        assert "Missing required variable" in str(exc_info.value)
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_load_system_prompt(tmp_path):
    """Test loading system prompts."""
    system_dir = tmp_path / "system"
    system_dir.mkdir()
    prompt_file = system_dir / "researcher.md"
    content = "You are a research assistant."
    prompt_file.write_text(content)
    
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        result = load_system_prompt('researcher')
        assert result == content
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_prompt_directory_structure():
    """Test that all required prompt directories exist."""
    required_dirs = ['research', 'generation', 'analysis', 'validation', 'system']
    
    for dir_name in required_dirs:
        dir_path = PROMPTS_DIR / dir_name
        assert dir_path.exists(), f"Directory {dir_name} should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"


@pytest.mark.unit
def test_prompt_files_exist():
    """Test that placeholder prompt files were created."""
    expected_prompts = {
        'research': ['search_companies.md', 'analyze_website.md', 'extract_products.md', 'categorize_products.md'],
        'generation': ['product_names.md', 'product_page.md', 'category_page.md', 'home_page.md', 'directory_entries.md', 'new_schema.md'],
        'analysis': ['schema_relevance.md', 'propose_schemas.md'],
        'validation': ['demo_features.md'],
        'system': ['researcher.md', 'generator.md', 'analyst.md']
    }
    
    for category, files in expected_prompts.items():
        for file_name in files:
            file_path = PROMPTS_DIR / category / file_name
            assert file_path.exists(), f"Prompt file {category}/{file_name} should exist"
            # Verify it's not empty
            content = file_path.read_text()
            assert len(content) > 0, f"Prompt file {category}/{file_name} should not be empty"


@pytest.mark.unit
def test_load_prompt_preserves_multiline():
    """Test that multiline prompts are preserved correctly."""
    # Use an actual prompt file from the system
    result = load_system_prompt('researcher')
    
    # Should contain multiple lines
    assert '\n' in result
    assert len(result) > 50  # Should be substantial content


@pytest.mark.unit
def test_load_prompt_with_empty_variables(tmp_path):
    """Test loading prompt with empty dict doesn't break."""
    test_category = tmp_path / "test_category"
    test_category.mkdir()
    prompt_file = test_category / "simple.md"
    content = "No variables here."
    prompt_file.write_text(content)
    
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        result = load_prompt('test_category', 'simple', {})
        assert result == content
    finally:
        loader_module.PROMPTS_DIR = original_dir


@pytest.mark.unit
def test_load_prompt_unicode_content(tmp_path):
    """Test that unicode content is handled correctly."""
    test_category = tmp_path / "test_category"
    test_category.mkdir()
    prompt_file = test_category / "unicode.md"
    content = "Hello 世界! Привет мир! 🚀"
    prompt_file.write_text(content, encoding='utf-8')
    
    import lib.llm.prompts.loader as loader_module
    original_dir = loader_module.PROMPTS_DIR
    loader_module.PROMPTS_DIR = tmp_path
    
    try:
        result = load_prompt('test_category', 'unicode')
        assert result == content
    finally:
        loader_module.PROMPTS_DIR = original_dir
