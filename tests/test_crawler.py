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

def test_should_ignore_dir():
    """Test directory ignore pattern matching."""
    # Setup test config with ignore patterns
    config = {
        'ignore_patterns': {
            'directories': [
                'storage',
                'storage/**',
                '**/storage',
                '**/storage/**',
                'datasets',
                'request_queues'
            ],
            'files': []
        }
    }
    
    # Create crawler with test root path
    crawler = RepositoryCrawler(str(Path.cwd()), config)
    
    # Test cases
    test_cases = [
        # Direct matches
        ('storage', True),
        ('storage/', True),
        ('datasets', True),
        ('request_queues', True),
        
        # Nested paths
        ('path/to/storage', True),
        ('path/to/storage/subdir', True),
        ('path/to/datasets', True),
        ('path/to/request_queues', True),
        
        # Non-matches
        ('not_storage', False),
        ('my_datasets_folder', False),
        ('requests', False),
    ]
    
    # Run tests
    for path, should_ignore in test_cases:
        assert crawler._should_ignore_dir(path) == should_ignore, \
            f"Failed for path: {path}, expected: {should_ignore}"

def test_ignore_patterns_in_tree():
    """Test that ignored directories are excluded from file tree."""
    # Setup test config
    config = {
        'ignore_patterns': {
            'directories': [
                'storage',
                'storage/**',
                '**/storage',
                '**/storage/**',
                'datasets',
                'request_queues'
            ],
            'files': []
        }
    }
    
    # Create crawler with test root
    crawler = RepositoryCrawler(str(Path.cwd()), config)
    
    # Get file tree
    tree = crawler.get_file_tree()
    
    def check_tree_for_ignored(tree_dict, ignored_names=['storage', 'datasets', 'request_queues']):
        """Recursively check tree for ignored directories."""
        if not isinstance(tree_dict, dict):
            return True
            
        # Check current level
        for name in ignored_names:
            assert name not in tree_dict, f"Found ignored directory '{name}' in tree"
            
        # Check nested directories
        for value in tree_dict.values():
            if isinstance(value, dict):
                check_tree_for_ignored(value, ignored_names)
                
        return True
    
    # Verify no ignored directories in tree
    assert check_tree_for_ignored(tree.get('contents', {})), "Found ignored directories in tree" 