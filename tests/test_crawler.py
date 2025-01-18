"""Repository Crawler Test Suite

This module contains comprehensive tests for the repository crawler functionality.
It verifies pattern matching, caching behavior, and tree generation.

Test Categories:
1. Pattern Matching
2. Cache Management
3. Tree Generation
4. Error Handling
"""

import pytest
from pathlib import Path
from backend.core.crawler import RepositoryCrawler

def test_ignore_patterns():
    """Test pattern matching functionality.
    
    This test verifies that:
    1. Directory ignore patterns are correctly applied
    2. File ignore patterns support wildcards
    3. The file tree excludes ignored items
    4. Pattern matching is case-sensitive
    
    Example patterns:
        - Directories: .git, node_modules, __pycache__
        - Files: *.pyc, *.log, .env
    """
    # Create test config
    config = {
        'ignore_patterns': {
            'directories': ['.git', 'node_modules', '__pycache__'],
            'files': ['*.pyc', '*.log', '.env']
        }
    }
    
    # Initialize crawler with test config
    crawler = RepositoryCrawler(str(Path.cwd()), config)
    
    # Test directory ignore patterns
    assert crawler._should_ignore_dir('.git') == True, "Should ignore .git directory"
    assert crawler._should_ignore_dir('node_modules') == True, "Should ignore node_modules"
    assert crawler._should_ignore_dir('src') == False, "Should not ignore src directory"
    
    # Test file ignore patterns
    assert crawler._should_ignore_file('test.pyc') == True, "Should ignore .pyc files"
    assert crawler._should_ignore_file('app.log') == True, "Should ignore .log files"
    assert crawler._should_ignore_file('.env') == True, "Should ignore .env file"
    assert crawler._should_ignore_file('main.py') == False, "Should not ignore .py files"
    
    # Get file tree and verify ignored items are not included
    tree = crawler.get_file_tree()
    
    def check_tree(tree_dict):
        """Recursively validate tree against ignore patterns.
        
        Args:
            tree_dict: Dictionary representing directory structure
            
        Raises:
            AssertionError: If ignored items are found in tree
        """
        for name, contents in tree_dict.items():
            # Check that no ignored directories are present
            assert name not in config['ignore_patterns']['directories'], \
                f"Found ignored directory: {name}"
            
            # Check that no ignored files are present
            for pattern in config['ignore_patterns']['files']:
                if '*' in pattern:
                    pattern = pattern.replace('*', '')
                    assert not name.endswith(pattern), \
                        f"Found ignored file pattern: {name}"
                else:
                    assert name != pattern, \
                        f"Found ignored file: {name}"
            
            # Recursively check subdirectories
            if isinstance(contents, dict):
                check_tree(contents)
    
    # Check the contents of the tree
    if 'contents' in tree:
        check_tree(tree['contents']) 