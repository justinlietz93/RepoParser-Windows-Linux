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
        logger.debug("Initializing FileViewer")
        
        # Store repo root
        self.repo_root = Path(repo_root) if repo_root else None
        logger.debug(f"Repository root: {self.repo_root}")
        
        # Normalize the file path
        if isinstance(file_path, str):
            logger.debug(f"Converting string path to Path object: {file_path}")
            file_path = Path(file_path)
        self.file_path = file_path
        
        logger.debug(f"Initialized FileViewer for {self.file_path}")
        if self.repo_root:
            logger.debug(f"Relative to repo root: {self.file_path.relative_to(self.repo_root) if self.file_path.is_relative_to(self.repo_root) else 'not relative'}")
    
    def get_language(self):
        """Get the programming language based on file extension.
        
        Returns:
            str: Language identifier for syntax highlighting
        """
        extension = self.file_path.suffix.lower()
        logger.debug(f"Detecting language for extension: {extension}")
        
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
        logger.debug(f"Detected language: {lang}")
        return lang
    
    def get_content(self):
        """Read and return the file contents.
        
        Returns:
            str: File contents or error message
        """
        try:
            if not self.repo_root:
                error_msg = "Repository root path not provided"
                logger.error(error_msg)
                return error_msg

            # Construct path relative to repository root
            file_path = self.repo_root / self.file_path
            logger.debug(f"Reading file from repository: {file_path}")
            
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                return error_msg
            
            if not file_path.is_file():
                error_msg = f"Not a file: {file_path}"
                logger.error(error_msg)
                return error_msg
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Successfully read {len(content)} characters from {file_path}")
                self.file_path = file_path
                return content
                
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
        logger.debug("Starting render")
        content = self.get_content()
        language = self.get_language()
        
        logger.debug(f"Rendering content with language: {language}")
        st.code(content, language=language)
        
        # File information
        st.markdown("---")
        st.markdown("### File Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"Path: {self.file_path}")
            if self.file_path.exists():
                size = self.file_path.stat().st_size
                logger.debug(f"File size: {size:,} bytes")
                st.text(f"Size: {size:,} bytes")
        
        with col2:
            st.text(f"Language: {language}")
            if self.file_path.exists():
                mtime = self.file_path.stat().st_mtime
                logger.debug(f"Last modified: {mtime}")
                st.text(f"Last modified: {mtime}") 