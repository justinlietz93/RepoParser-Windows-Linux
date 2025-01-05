from typing import Dict, List, Tuple, Optional
import os
import logging
import fnmatch
import yaml
from pathlib import Path

class RepositoryCrawler:
    """Handles repository traversal and file analysis."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the crawler with configuration."""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise
            
    def crawl(self, root_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """
        Crawl the repository and generate directory tree.
        
        Args:
            root_path: Path to repository root
            
        Returns:
            Tuple containing directory tree string and list of file paths
        """
        self.logger.info(f"Starting repository crawl at: {root_path}")
        return self._build_directory_tree(
            root_path,
            self.config['included_extensions'],
            self.config['ignore_patterns']
        )
        
    def _build_directory_tree(
        self,
        root_path: str,
        included_extensions: List[str],
        ignore_patterns: Dict[str, List[str]],
        indent: int = 0
    ) -> Tuple[str, List[Tuple[int, str]]]:
        """Build directory tree structure."""
        tree_str = ""
        file_paths = []
        
        try:
            items = sorted(os.listdir(root_path))
        except PermissionError:
            self.logger.warning(f"Permission denied: {root_path}")
            return tree_str, file_paths
            
        for item in items:
            item_path = Path(root_path) / item
            
            if item_path.is_dir():
                if self._should_ignore_dir(item, ignore_patterns):
                    continue
                    
                tree_str += '    ' * indent + f"[{item}/]\n"
                sub_tree, sub_paths = self._build_directory_tree(
                    str(item_path),
                    included_extensions,
                    ignore_patterns,
                    indent + 1
                )
                tree_str += sub_tree
                file_paths.extend(sub_paths)
            else:
                if self._should_ignore_file(item, ignore_patterns):
                    continue
                    
                tree_str += '    ' * indent + f"{item}\n"
                if self._is_included_file(item, included_extensions):
                    file_paths.append((indent, str(item_path)))
                    
        return tree_str, file_paths
        
    def _should_ignore_dir(self, dirname: str, ignore_patterns: Dict[str, List[str]]) -> bool:
        """Check if directory should be ignored."""
        return any(fnmatch.fnmatch(dirname, pattern) 
                  for pattern in ignore_patterns['directories'])
                  
    def _should_ignore_file(self, filename: str, ignore_patterns: Dict[str, List[str]]) -> bool:
        """Check if file should be ignored."""
        return any(fnmatch.fnmatch(filename, pattern) 
                  for pattern in ignore_patterns['files'])
                  
    def _is_included_file(self, filename: str, extensions: List[str]) -> bool:
        """Check if file should be included based on extension."""
        return any(filename.lower().endswith(ext) for ext in extensions) 