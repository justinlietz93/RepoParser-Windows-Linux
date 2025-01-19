"""Repository Crawler Core Module

This module implements the core repository traversal and analysis functionality.
It provides efficient caching, configurable ignore patterns, and robust error handling.

Example:
    ```python
    config = {
        'ignore_patterns': {
            'directories': ['.git', '__pycache__'],
            'files': ['*.pyc', '*.log']
        }
    }
    crawler = RepositoryCrawler('/path/to/repo', config)
    file_tree = crawler.get_file_tree()
    ```
"""

from typing import Dict, List, Tuple, Optional, Any
import os
import logging
import fnmatch
import yaml
from pathlib import Path
from datetime import datetime

# Just get the logger, don't configure it
logger = logging.getLogger(__name__)

class RepositoryCrawler:
    """Repository traversal and analysis engine.
    
    This class handles repository exploration, file analysis, and tree generation
    with efficient caching and configurable ignore patterns.
    
    Attributes:
        root_path (Path): Root directory path to analyze
        config (Dict): Configuration dictionary with ignore patterns
        _file_tree_cache (Optional[Dict]): Cached file tree structure
        _config_hash (Optional[str]): Hash of current configuration
    """
    
    def __init__(self, root_path: str, config: Dict[str, Any]):
        """Initialize the repository crawler.
        
        Args:
            root_path: Path to the repository root directory
            config: Configuration dictionary containing ignore patterns
            
        Raises:
            ValueError: If root_path doesn't exist or isn't a directory
            TypeError: If config is not properly structured
        """
        self.root_path = Path(root_path)
        
        # Deep copy config to prevent reference issues
        self.config = {
            'ignore_patterns': {
                'directories': list(config.get('ignore_patterns', {}).get('directories', [])),
                'files': list(config.get('ignore_patterns', {}).get('files', []))
            }
        }
        
        # Cache for file tree to prevent unnecessary recalculation
        self._file_tree_cache = None
        self._config_hash = None
        
        logger.info("Starting Repository Crawler")
        logger.debug(f"Initialized with root: {root_path}")
        logger.debug(f"Config: {self.config}")
        
    def _get_config_hash(self) -> str:
        """Generate a reliable hash of current config for cache invalidation.
        
        Returns:
            str: Hash string representing current configuration
            
        Note:
            This method ensures consistent hashing by sorting pattern lists
            and using a stable string representation.
        """
        try:
            # Sort lists to ensure consistent hashing
            sorted_config = {
                'ignore_patterns': {
                    'directories': sorted(self.config['ignore_patterns']['directories']),
                    'files': sorted(self.config['ignore_patterns']['files'])
                }
            }
            # Use stable string representation
            config_str = f"dirs:{','.join(sorted_config['ignore_patterns']['directories'])}|files:{','.join(sorted_config['ignore_patterns']['files'])}"
            return str(hash(config_str))
        except Exception as e:
            logger.error(f"Error calculating config hash: {str(e)}")
            # Return unique hash to invalidate cache
            return str(hash(str(datetime.now())))
            
    def _invalidate_cache(self):
        """Safely invalidate the file tree cache."""
        self._file_tree_cache = None
        self._config_hash = None
        
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update crawler configuration with validation and proper cache management."""
        try:
            # Validate new config structure
            if not isinstance(new_config.get('ignore_patterns'), dict):
                logger.error("Invalid ignore_patterns structure in new config")
                return False
                
            # Extract and validate patterns
            new_dirs = list(new_config.get('ignore_patterns', {}).get('directories', []))
            new_files = list(new_config.get('ignore_patterns', {}).get('files', []))
            
            if not all(isinstance(p, str) for p in new_dirs + new_files):
                logger.error("Invalid pattern type found - all patterns must be strings")
                return False
                
            # Update with validated data
            self.config = {
                'ignore_patterns': {
                    'directories': new_dirs,
                    'files': new_files
                }
            }
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info("Configuration updated successfully")
            logger.debug(f"New config: {self.config}")
            return True
            
        except Exception as e:
            logger.exception("Error updating configuration")
            return False
            
    def get_file_tree(self) -> Dict:
        """Get the repository file tree structure with caching.
        
        Returns:
            Dict: Tree structure of repository files and directories
        """
        try:
            # Check if we have a valid cached tree
            current_hash = self._get_config_hash()
            if self._file_tree_cache is not None and self._config_hash == current_hash:
                logger.debug("Using cached file tree")
                return self._file_tree_cache

            logger.info("Generating new file tree structure")
            
            # Initialize tree with root info
            tree = {
                'type': 'directory',
                'name': self.root_path.name,
                'path': str(self.root_path),
                'contents': {}
            }
            
            # Build tree with early ignore checks
            try:
                self._build_tree_dict(self.root_path, tree['contents'])
                logger.info("File tree generated successfully")
            except Exception as e:
                logger.error(f"Error building file tree: {str(e)}")
                tree['error'] = str(e)
            
            # Cache the result
            self._file_tree_cache = tree
            self._config_hash = current_hash
            
            return tree
            
        except Exception as e:
            logger.error(f"Error in get_file_tree: {str(e)}")
            return {
                'type': 'error',
                'message': f"Failed to generate file tree: {str(e)}"
            }
            
    def _build_tree_dict(self, path: Path, tree: Dict) -> None:
        """Recursively build a dictionary representation of the directory tree."""
        try:
            items = []
            try:
                # First try to list directory contents
                items = sorted(path.iterdir())
            except PermissionError:
                logger.warning(f"Permission denied accessing: {path}")
                tree['__error__'] = 'Permission denied'
                return
            except OSError as e:
                logger.warning(f"OS error accessing {path}: {e}")
                tree['__error__'] = f'Access error: {str(e)}'
                return
                
            for item in items:
                try:
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
                except Exception as e:
                    logger.error(f"Error processing item {item}: {str(e)}")
                    tree[f"{item.name} (error)"] = f"Error: {str(e)}"
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing directory {path}: {str(e)}")
            tree['__error__'] = f'Processing error: {str(e)}'
            
    def _should_ignore_dir(self, dirname: str) -> bool:
        """Check if directory should be ignored with proper error handling."""
        try:
            patterns = self.config.get('ignore_patterns', {}).get('directories', [])
            if not patterns:
                return False
                
            # Convert to Path and get relative path
            dir_path = Path(dirname)
            if not dir_path.is_absolute():
                dir_path = self.root_path / dir_path
                
            try:
                # Get relative path for matching
                rel_path = str(dir_path.relative_to(self.root_path))
                # Normalize path separators
                rel_path = rel_path.replace('\\', '/')
                
                # Add variations of the path for matching
                paths_to_check = [
                    rel_path,                    # normal path
                    f"/{rel_path}",              # with leading slash
                    f"{rel_path}/",              # with trailing slash
                    f"/{rel_path}/",             # with both slashes
                ]
                
                # Check each pattern against all path variations
                for pattern in patterns:
                    pattern = pattern.replace('\\', '/')
                    
                    # Remove leading/trailing slashes from pattern for consistent matching
                    pattern = pattern.strip('/')
                    
                    # Direct name match (for backwards compatibility)
                    if pattern.lower() == dir_path.name.lower():
                        logger.debug(f"Directory name matches pattern exactly: {dir_path.name} == {pattern}")
                        return True
                    
                    # Check all path variations
                    for path_var in paths_to_check:
                        # Direct match
                        if pattern.lower() == path_var.lower():
                            logger.debug(f"Directory path matches pattern exactly: {path_var} == {pattern}")
                            return True
                            
                        # Wildcard match
                        if fnmatch.fnmatch(path_var.lower(), pattern.lower()):
                            logger.debug(f"Directory path matches wildcard: {path_var} matches {pattern}")
                            return True
                            
                        # Handle **/ prefix (match any parent directory)
                        if pattern.startswith('**/'):
                            suffix = pattern[3:]  # Remove **/
                            if fnmatch.fnmatch(path_var.lower(), f"*/{suffix}".lower()):
                                logger.debug(f"Directory matches **/ pattern: {path_var} matches {pattern}")
                                return True
                                
                        # Handle /** suffix (match any subdirectory)
                        if pattern.endswith('/**'):
                            prefix = pattern[:-3]  # Remove /**
                            if path_var.lower().startswith(prefix.lower()):
                                logger.debug(f"Directory matches /** pattern: {path_var} matches {pattern}")
                                return True
                                
                return False
                
            except ValueError as e:
                # If we can't get relative path, just check the name
                logger.debug(f"Falling back to name-only match for {dirname}: {e}")
                return any(fnmatch.fnmatch(dir_path.name.lower(), pattern.lower()) for pattern in patterns)
                
        except Exception as e:
            logger.error(f"Error in _should_ignore_dir: {e}")
            return False
            
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored with proper error handling."""
        try:
            patterns = self.config.get('ignore_patterns', {}).get('files', [])
            
            # Convert to relative path for matching
            file_path = Path(filename)
            if not file_path.is_absolute():
                file_path = self.root_path / file_path
                
            try:
                rel_path = str(file_path.relative_to(self.root_path))
                logger.debug(f"Checking file: {rel_path}")
                
                # Check exact matches first
                if rel_path in patterns:
                    logger.debug(f"File {rel_path} exactly matches ignore pattern")
                    return True
                    
                # Then check pattern matches
                for pattern in patterns:
                    try:
                        if fnmatch.fnmatch(rel_path, pattern):
                            logger.debug(f"File {rel_path} matches pattern {pattern}")
                            return True
                    except Exception as e:
                        logger.warning(f"Error matching pattern {pattern}: {str(e)}")
                        continue
                        
                # Check if any parent directory is ignored
                current = file_path.parent
                while current != self.root_path and current != current.parent:
                    try:
                        current_rel = str(current.relative_to(self.root_path))
                        if current_rel in self.config.get('ignore_patterns', {}).get('directories', []):
                            logger.debug(f"File {rel_path} ignored via parent directory {current_rel}")
                            return True
                    except ValueError:
                        break
                    except Exception as e:
                        logger.warning(f"Error checking parent directory {current}: {str(e)}")
                        break
                    current = current.parent
                    
                return False
                
            except ValueError:
                logger.warning(f"File {file_path} is not relative to root {self.root_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking file ignore status: {str(e)}")
            return False

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