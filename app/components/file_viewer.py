import streamlit as st
from pathlib import Path

class FileViewer:
    def __init__(self, file_path):
        """Initialize the file viewer.
        
        Args:
            file_path (str): Path to the file to view
        """
        self.file_path = Path(file_path)
    
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
        return language_map.get(extension, 'text')
    
    def get_content(self):
        """Read and return the file contents.
        
        Returns:
            str: File contents or error message
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "Unable to decode file contents. This might be a binary file."
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
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
            st.text(f"Size: {self.file_path.stat().st_size:,} bytes")
        
        with col2:
            st.text(f"Language: {language}")
            st.text(f"Last modified: {self.file_path.stat().st_mtime}") 