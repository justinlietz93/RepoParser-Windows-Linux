from typing import Dict, List, Tuple, Optional
import os
import logging
import fnmatch
import yaml
from pathlib import Path

# Just get the logger, don't configure it
logger = logging.getLogger(__name__)

class RepositoryCrawler:
    """Handles repository traversal and file analysis."""
    
    def __init__(self, root_path: str, config: Optional[Dict] = None):
        """
        Initialize the crawler.
        
        Args:
            root_path: Path to repository root
            config: Configuration dictionary. If None, loads from config.yaml
        """
        self.root_path = Path(root_path)
        logger.info(f"Initializing crawler for: {self.root_path}")
        
        if config is None:
            self.config = self._load_config(str(Path(__file__).parent.parent.parent / 'config' / 'config.yaml'))
        else:
            self.config = config
            
        # Ensure ignore_patterns exists
        if 'ignore_patterns' not in self.config:
            self.config['ignore_patterns'] = {'directories': [], 'files': []}
            
        logger.info(f"Ignoring {len(self.config.get('ignore_patterns', {}).get('directories', []))} directories and {len(self.config.get('ignore_patterns', {}).get('files', []))} file patterns")
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file."""
        try:
            logger.debug(f"Loading config from: {config_path}")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.debug("Config loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            raise
            
    def get_file_tree(self) -> Dict:
        """
        Generate a hierarchical file tree structure.
        
        Returns:
            Dictionary representing the file tree with root path
        """
        logger.info("Generating file tree structure")
        tree = {
            'path': str(self.root_path),
            'contents': {}
        }
        try:
            self._build_tree_dict(self.root_path, tree['contents'])
            logger.info("File tree generated successfully")
            return tree
        except Exception as e:
            logger.error(f"Error generating file tree: {str(e)}")
            raise
            
    def _build_tree_dict(self, path: Path, tree: Dict) -> None:
        """Recursively build a dictionary representation of the directory tree."""
        try:
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    if self._should_ignore_dir(item.name):
                        logger.debug(f"Ignoring directory: {item}")
                        continue
                    logger.debug(f"Processing directory: {item}")
                    tree[item.name] = {}
                    self._build_tree_dict(item, tree[item.name])
                else:
                    if self._should_ignore_file(item.name):
                        logger.debug(f"Ignoring file: {item}")
                        continue
                    logger.debug(f"Including file: {item}")
                    tree[item.name] = None
        except PermissionError:
            logger.warning(f"Permission denied accessing: {path}")
        except Exception as e:
            logger.error(f"Error processing directory {path}: {str(e)}")
            raise
                  
    def _should_ignore_dir(self, dirname: str) -> bool:
        """Check if directory should be ignored."""
        patterns = self.config.get('ignore_patterns', {}).get('directories', [])
        # Use full path for matching to handle nested directories
        full_path = str(Path(dirname))
        should_ignore = any(
            fnmatch.fnmatch(part, pattern)
            for pattern in patterns
            for part in full_path.split(os.sep)
        )
        if should_ignore:
            logger.debug(f"Directory {dirname} matches ignore pattern")
        return should_ignore
                  
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored."""
        patterns = self.config.get('ignore_patterns', {}).get('files', [])
        # Use full path for matching to handle nested files
        full_path = str(Path(filename))
        should_ignore = any(
            fnmatch.fnmatch(full_path, pattern) or
            any(fnmatch.fnmatch(part, pattern) for part in full_path.split(os.sep))
            for pattern in patterns
        )
        if should_ignore:
            logger.debug(f"File {filename} matches ignore pattern")
        return should_ignore

    def walk(self) -> List[Tuple[str, int]]:
        """
        Walk through the repository and collect file information.
        
        Returns:
            List of tuples containing (file_path, size_in_bytes)
        """
        logger.info("Walking repository for file information")
        files_info = []
        
        try:
            for root, dirs, files in os.walk(self.root_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                        
                    try:
                        file_path = Path(root) / file
                        if file_path.is_file():  # Verify it's still a file (symlinks, etc.)
                            rel_path = file_path.relative_to(self.root_path)
                            size = file_path.stat().st_size
                            files_info.append((str(rel_path), size))
                    except Exception as e:
                        logger.warning(f"Error processing file {file}: {str(e)}")
                        continue
            
            logger.info(f"Found {len(files_info)} files in repository")
            return files_info
            
        except Exception as e:
            logger.error(f"Error walking repository: {str(e)}")
            raise 