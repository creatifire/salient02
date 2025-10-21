#!/usr/bin/env python3
"""
Script to add copyright headers to all Python files.

Copyright (c) 2025 Ape4, Inc. All rights reserved.
"""

import os
from pathlib import Path
from datetime import datetime

COPYRIGHT_HEADER_PYTHON = '''"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

'''

COPYRIGHT_HEADER_MARKDOWN = '''<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

'''

# Directories to process
INCLUDE_DIRS = [
    "backend/app",
    "backend/scripts",
    "backend/tests",
    "memorybank",
]

# Directories to skip
EXCLUDE_DIRS = [
    "__pycache__",
    ".pytest_cache",
    "venv",
    "node_modules",
    ".git",
    "htmlcov",
    "migrations/versions",  # Skip Alembic migration files
]

# Files to skip
EXCLUDE_FILES = [
    "__init__.py",  # Keep __init__.py files minimal
]


def should_process_file(filepath: Path) -> bool:
    """Check if file should be processed."""
    # Skip if in excluded directory
    for exclude in EXCLUDE_DIRS:
        if exclude in filepath.parts:
            return False
    
    # Skip if excluded filename
    if filepath.name in EXCLUDE_FILES:
        return False
    
    # Only process .py and .md files
    if filepath.suffix not in [".py", ".md"]:
        return False
    
    return True


def has_copyright_header(content: str) -> bool:
    """Check if file already has Ape4 copyright header."""
    return "Copyright (c) 2025 Ape4, Inc." in content


def add_header_to_file(filepath: Path, dry_run: bool = False) -> bool:
    """Add copyright header to a Python or Markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has header
        if has_copyright_header(content):
            return False
        
        # Determine file type and appropriate header
        if filepath.suffix == ".md":
            header = COPYRIGHT_HEADER_MARKDOWN
            # For Markdown, just prepend at the top
            new_content = header + content
        
        elif filepath.suffix == ".py":
            header = COPYRIGHT_HEADER_PYTHON
            # Handle shebang
            if content.startswith('#!'):
                lines = content.split('\n', 1)
                new_content = lines[0] + '\n' + header + (lines[1] if len(lines) > 1 else '')
            # Handle existing docstring
            elif content.startswith('"""') or content.startswith("'''"):
                # Find end of existing docstring
                quote = '"""' if content.startswith('"""') else "'''"
                end_idx = content.find(quote, 3)
                if end_idx != -1:
                    # Add copyright after existing docstring
                    new_content = content[:end_idx + 3] + '\n' + header + content[end_idx + 3:]
                else:
                    # Malformed docstring, add at top
                    new_content = header + content
            else:
                # Add at the very top
                new_content = header + content
        else:
            return False
        
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return True
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Process all Python and Markdown files and add copyright headers."""
    repo_root = Path(__file__).parent.parent
    
    print(f"🔍 Scanning repository: {repo_root}")
    print(f"📁 Include directories: {', '.join(INCLUDE_DIRS)}")
    print(f"⏭️  Exclude directories: {', '.join(EXCLUDE_DIRS)}")
    print()
    
    files_to_process = []
    
    # Collect all Python and Markdown files
    for include_dir in INCLUDE_DIRS:
        dir_path = repo_root / include_dir
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {include_dir}")
            continue
        
        for file in dir_path.rglob("*"):
            if file.is_file() and should_process_file(file):
                files_to_process.append(file)
    
    print(f"📝 Found {len(files_to_process)} files to process (.py and .md)")
    print()
    
    # Process files
    updated_count = 0
    skipped_count = 0
    
    for filepath in sorted(files_to_process):
        relative_path = filepath.relative_to(repo_root)
        
        if add_header_to_file(filepath, dry_run=False):
            print(f"✅ Added header: {relative_path}")
            updated_count += 1
        else:
            print(f"⏭️  Skipped (has header): {relative_path}")
            skipped_count += 1
    
    print()
    print(f"✨ Summary:")
    print(f"   Updated: {updated_count} files")
    print(f"   Skipped: {skipped_count} files")
    print(f"   Total:   {len(files_to_process)} files")


if __name__ == "__main__":
    main()

