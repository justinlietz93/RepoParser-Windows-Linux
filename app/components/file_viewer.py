import streamlit as st
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class FileViewer:
    def __init__(self, file_path, repo_root=None):
        """Initialize the file viewer.
        
        Args:
            file_path (str): Path to the file to view
            repo_root (str, optional): Root path of the repository
        """
        # Store repo root
        self.repo_root = Path(repo_root) if repo_root else None
        
        # Normalize the file path
        if isinstance(file_path, str):
            file_path = Path(file_path)
        self.file_path = file_path
        
        logger.debug(f"Initializing FileViewer for {self.file_path} (repo root: {self.repo_root})")
    
    def get_language(self):
        """Get the programming language based on file extension.
        
        Returns:
            str: Language identifier for syntax highlighting
        """
        extension = self.file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.bash': 'bash',
            '.sql': 'sql',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.r': 'r',
            '.dockerfile': 'dockerfile',
            '.xml': 'xml',
        }
        lang = language_map.get(extension, 'text')
        logger.debug(f"Detected language {lang} for file {self.file_path}")
        return lang
    
    def get_content(self):
        """Read and return the file contents.
        
        Returns:
            str: File contents or error message
        """
        try:
            logger.debug(f"Attempting to read file: {self.file_path}")
            
            # Build list of possible paths
            possible_paths = []
            
            # Try as absolute path first
            if self.file_path.is_absolute():
                possible_paths.append(self.file_path)
            
            # Try relative to repo root if available
            if self.repo_root:
                possible_paths.append(self.repo_root / self.file_path)
            
            # Try relative to current directory
            possible_paths.append(Path.cwd() / self.file_path)
            
            # Log all paths we're going to try
            logger.debug(f"Trying paths: {[str(p) for p in possible_paths]}")
            
            for path in possible_paths:
                try:
                    if path.exists() and path.is_file():
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            logger.debug(f"Successfully read {len(content)} characters from {path}")
                            # Store the successful path
                            self.file_path = path
                            return content
                except Exception as e:
                    logger.debug(f"Failed to read {path}: {str(e)}")
                    continue
            
            error_msg = f"File not found: {self.file_path}"
            logger.error(error_msg)
            return error_msg
                
        except UnicodeDecodeError as e:
            error_msg = f"Unable to decode file {self.file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        except PermissionError as e:
            error_msg = f"Permission denied reading {self.file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Error reading file {self.file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def render(self):
        """Render the file contents with syntax highlighting."""
        content = self.get_content()
        language = self.get_language()
        
        st.code(content, language=language)
        
        # File information
        st.markdown("---")
        st.markdown("### File Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"Path: {self.file_path}")
            if self.file_path.exists():
                st.text(f"Size: {self.file_path.stat().st_size:,} bytes")
        
        with col2:
            st.text(f"Language: {language}")
            if self.file_path.exists():
                st.text(f"Last modified: {self.file_path.stat().st_mtime}") 