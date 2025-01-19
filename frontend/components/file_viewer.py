import streamlit as st
from pathlib import Path
import logging
import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FileViewer:
    def __init__(self, file_path: str, repo_root: Optional[str] = None):
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
    
    def get_language(self) -> str:
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
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get file information including size, modification time, etc.
        
        Returns:
            Dict[str, Any]: Dictionary containing file information
        """
        try:
            stat = self.file_path.stat()
            return {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_binary': self._is_binary(),
                'language': self.get_language(),
                'relative_path': str(self.file_path.relative_to(self.repo_root)) if self.repo_root else str(self.file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {}
    
    def _is_binary(self, sample_size: int = 1024) -> bool:
        """Check if file appears to be binary.
        
        Args:
            sample_size (int): Number of bytes to check
            
        Returns:
            bool: True if file appears to be binary
        """
        try:
            with open(self.file_path, 'rb') as f:
                chunk = f.read(sample_size)
                # Check for null bytes and high concentration of non-ASCII
                if b'\x00' in chunk:
                    return True
                # More than 30% non-ASCII characters suggests binary
                non_ascii = len([b for b in chunk if b > 127])
                return non_ascii > len(chunk) * 0.3
        except Exception:
            return True
    
    def get_content(self, max_size: int = 1024 * 1024) -> Optional[str]:
        """Read and return the file contents.
        
        Args:
            max_size (int): Maximum file size to read in bytes
            
        Returns:
            Optional[str]: File contents or None if error
        """
        try:
            # Handle both absolute and relative paths
            file_path = Path(self.file_path)
            if not file_path.is_absolute() and self.repo_root:
                file_path = self.repo_root / file_path
            
            logger.debug(f"Reading file: {file_path}")
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            if not file_path.is_file():
                logger.error(f"Not a file: {file_path}")
                return None
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_size:
                return f"File is too large ({file_size / (1024*1024):.1f} MB). Please use a text editor for large files."
            
            # Check if binary
            if self._is_binary():
                return "This appears to be a binary file and cannot be displayed"
            
            # Read file safely
            content = []
            with open(file_path, 'r', encoding='utf-8') as f:
                while chunk := f.read(8192):  # 8KB chunks
                    content.append(chunk)
                    if len(''.join(content)) > max_size:
                        content.append("\n... File truncated (too large) ...")
                        break
                return ''.join(content)
                
        except UnicodeDecodeError:
            logger.error(f"Unable to decode file {self.file_path}")
            return "Unable to decode file - this may be a binary file"
            
        except PermissionError as e:
            logger.error(f"Permission denied reading {self.file_path}: {str(e)}")
            return f"Permission denied reading file: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {str(e)}")
            return f"Error reading file: {str(e)}"
    
    def calculate_tokens(self, content: str) -> Tuple[int, float]:
        """Calculate tokens and cost based on selected model."""
        if 'llm_provider' not in st.session_state.config or 'model' not in st.session_state.config:
            return 0, 0.0
            
        provider = st.session_state.config.get('llm_provider')
        model = st.session_state.config.get('model')
        
        if not provider or not model:
            return 0, 0.0
            
        try:
            # Model context limits
            context_limits = {
                "gpt-4": 8192,
                "gpt-4-32k": 32768,
                "gpt-4-turbo": 128000,
                "gpt-3.5-turbo": 16384,
                "gpt-3.5-turbo-16k": 16384,
                "claude-2.1": 200000,
                "claude-instant": 100000,
                "deepseek-chat": 32768,
                "gemini-1.5-pro-latest": 1000000
            }
            
            if provider == "OpenAI":
                import tiktoken
                encoding = tiktoken.encoding_for_model(model)
                token_count = len(encoding.encode(content))
                # OpenAI pricing per 1k tokens
                costs = {
                    "gpt-4": 0.03,
                    "gpt-4-32k": 0.06,
                    "gpt-4-turbo": 0.01,
                    "gpt-3.5-turbo": 0.002,
                    "gpt-3.5-turbo-16k": 0.004
                }
                cost = (token_count / 1000) * costs.get(model, 0.0)
                return token_count, cost
                
            elif provider == "Anthropic":
                # Use Claude's tokenizer if available
                try:
                    from anthropic import Anthropic
                    client = Anthropic(api_key=st.session_state.config['api_keys'].get('ANTHROPIC_API_KEY', [''])[0])
                    token_count = client.count_tokens(content)
                except:
                    # Fallback to cl100k_base encoding which Claude uses
                    import tiktoken
                    encoding = tiktoken.get_encoding("cl100k_base")
                    token_count = len(encoding.encode(content))
                
                # Claude pricing per 1k tokens
                costs = {
                    "claude-2.1": 0.008,
                    "claude-instant": 0.0008
                }
                cost = (token_count / 1000) * costs.get(model, 0.0)
                return token_count, cost
                
            elif provider == "DeepSeek":
                # DeepSeek uses GPT tokenization
                import tiktoken
                encoding = tiktoken.get_encoding("cl100k_base")
                token_count = len(encoding.encode(content))
                # DeepSeek pricing per 1k tokens
                costs = {
                    "deepseek-chat": 0.002
                }
                cost = (token_count / 1000) * costs.get(model, 0.0)
                return token_count, cost
                
            elif provider == "Gemini":
                # Use approximate token counting for Gemini
                import tiktoken
                encoding = tiktoken.get_encoding("cl100k_base")
                token_count = len(encoding.encode(content))
                
                # Gemini pricing per 1k tokens
                costs = {
                    "gemini-1.5-pro-latest": 0.0005
                }
                cost = (token_count / 1000) * costs.get(model, 0.0)
                return token_count, cost
                
            return 0, 0.0
            
        except Exception as e:
            logger.error(f"Error calculating tokens: {str(e)}")
            return 0, 0.0

    def render_token_info(self, content: str):
        """Render token count and cost information."""
        if 'llm_provider' not in st.session_state.config or 'model' not in st.session_state.config:
            st.info("Select a model in LLM Settings to calculate tokens and cost")
            return
            
        provider = st.session_state.config.get('llm_provider')
        model = st.session_state.config.get('model')
        
        if not provider or not model:
            st.info("Select a model in LLM Settings to calculate tokens and cost")
            return
            
        tokens, cost = self.calculate_tokens(content)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tokens", f"{tokens:,}")
        with col2:
            st.metric("Estimated Cost", f"${cost:.4f}")
        with col3:
            context_limits = {
                "gpt-4": 8192,
                "gpt-4-32k": 32768,
                "gpt-4-turbo": 128000,
                "gpt-3.5-turbo": 16384,
                "gpt-3.5-turbo-16k": 16384,
                "claude-2.1": 200000,
                "claude-instant": 100000,
                "deepseek-chat": 32768,
                "gemini-1.5-pro-latest": 1000000
            }
            limit = context_limits.get(model, 0)
            st.metric("Model Limit", f"{limit:,}")
            
        st.caption(f"Using {provider} - {model}")
    
    def render(self):
        """Render the file contents with syntax highlighting and metadata."""
        logger.debug("Starting render")
        
        # Get file info first
        file_info = self.get_file_info()
        
        # Show file path and metadata
        st.markdown("### File Information")
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown(f"**Path:** `{file_info.get('relative_path', 'Unknown')}`")
            st.markdown(f"**Size:** {file_info.get('size', 0):,} bytes")
            
        with cols[1]:
            st.markdown(f"**Type:** {file_info.get('language', 'Unknown').title()}")
            st.markdown(f"**Binary:** {'Yes' if file_info.get('is_binary', False) else 'No'}")
            
        with cols[2]:
            st.markdown(f"**Modified:** {file_info.get('modified', 'Unknown')}")
            st.markdown(f"**Created:** {file_info.get('created', 'Unknown')}")
        
        st.markdown("---")
        
        # Get and display content
        content = self.get_content()
        if content:
            st.markdown("### File Content")
            st.code(content, language=file_info.get('language', 'text'))
        else:
            st.error("Unable to read file contents") 