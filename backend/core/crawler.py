from typing import Dict, List, Tuple, Optional
import os
import logging
import fnmatch
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class RepositoryCrawler:
    """Handles repository traversal and file analysis."""
    
    def __init__(self, root_path: str, config: Optional[Dict] = None):
        """
        Initialize the crawler.
        
        Args:
            root_path: Path to repository root
            config: Configuration dictionary. If None, loads from config.yaml
        """
        self.logger = logging.getLogger(__name__)
        self.root_path = Path(root_path)
        self.logger.info(f"Initializing RepositoryCrawler for path: {self.root_path}")
        
        if config is None:
            self.logger.debug("No config provided, loading from config.yaml")
            self.config = self._load_config(str(Path(__file__).parent.parent.parent / 'config' / 'config.yaml'))
        else:
            self.logger.debug("Using provided config dictionary")
            self.config = config
            
        # Ensure ignore_patterns exists
        if 'ignore_patterns' not in self.config:
            self.config['ignore_patterns'] = {'directories': [], 'files': []}
            
        self.logger.info(f"Ignoring {len(self.config.get('ignore_patterns', {}).get('directories', []))} directories")
        self.logger.info(f"Ignoring {len(self.config.get('ignore_patterns', {}).get('files', []))} file patterns")
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file."""
        try:
            self.logger.debug(f"Loading config from: {config_path}")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.debug("Config loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Error loading config from {config_path}: {str(e)}")
            raise
            
    def get_file_tree(self) -> Dict:
        """
        Generate a hierarchical file tree structure.
        
        Returns:
            Dictionary representing the file tree
        """
        self.logger.info("Generating file tree structure")
        tree = {}
        try:
            self._build_tree_dict(self.root_path, tree)
            self.logger.info("File tree generated successfully")
            return tree
        except Exception as e:
            self.logger.error(f"Error generating file tree: {str(e)}")
            raise
            
    def _build_tree_dict(self, path: Path, tree: Dict) -> None:
        """Recursively build a dictionary representation of the directory tree."""
        try:
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    if self._should_ignore_dir(item.name):
                        self.logger.debug(f"Ignoring directory: {item}")
                        continue
                    self.logger.debug(f"Processing directory: {item}")
                    tree[item.name] = {}
                    self._build_tree_dict(item, tree[item.name])
                else:
                    if self._should_ignore_file(item.name):
                        self.logger.debug(f"Ignoring file: {item}")
                        continue
                    self.logger.debug(f"Including file: {item}")
                    tree[item.name] = None
        except PermissionError:
            self.logger.warning(f"Permission denied accessing: {path}")
        except Exception as e:
            self.logger.error(f"Error processing directory {path}: {str(e)}")
            raise
                  
    def _should_ignore_dir(self, dirname: str) -> bool:
        """Check if directory should be ignored."""
        patterns = self.config.get('ignore_patterns', {}).get('directories', [])
        should_ignore = any(fnmatch.fnmatch(dirname, pattern) for pattern in patterns)
        if should_ignore:
            self.logger.debug(f"Directory {dirname} matches ignore pattern")
        return should_ignore
                  
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored."""
        patterns = self.config.get('ignore_patterns', {}).get('files', [])
        should_ignore = any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)
        if should_ignore:
            self.logger.debug(f"File {filename} matches ignore pattern")
        return should_ignore 