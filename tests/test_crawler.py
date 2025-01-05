import pytest
from pathlib import Path
from backend.core.crawler import RepositoryCrawler

def test_ignore_patterns():
    """Test that ignore patterns are correctly applied."""
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
    assert crawler._should_ignore_dir('.git') == True
    assert crawler._should_ignore_dir('node_modules') == True
    assert crawler._should_ignore_dir('src') == False
    
    # Test file ignore patterns
    assert crawler._should_ignore_file('test.pyc') == True
    assert crawler._should_ignore_file('app.log') == True
    assert crawler._should_ignore_file('.env') == True
    assert crawler._should_ignore_file('main.py') == False
    
    # Get file tree and verify ignored items are not included
    tree = crawler.get_file_tree()
    
    def check_tree(tree_dict):
        """Recursively check tree for ignored items."""
        for name, contents in tree_dict.items():
            # Check that no ignored directories are present
            assert name not in config['ignore_patterns']['directories']
            
            # Check that no ignored files are present
            for pattern in config['ignore_patterns']['files']:
                if '*' in pattern:
                    pattern = pattern.replace('*', '')
                    assert not name.endswith(pattern)
                else:
                    assert name != pattern
            
            # Recursively check subdirectories
            if isinstance(contents, dict):
                check_tree(contents)
    
    # Check the contents of the tree
    if 'contents' in tree:
        check_tree(tree['contents']) 