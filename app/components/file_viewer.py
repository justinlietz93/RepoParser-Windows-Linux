import streamlit as st
from typing import List, Tuple, Optional
from core.file_handler import FileHandler

def render_file_viewer(
    file_paths: List[Tuple[int, str]], 
    file_handler: FileHandler
) -> Optional[str]:
    """
    Render the file contents viewer.
    
    Args:
        file_paths: List of tuples containing indent level and file path
        file_handler: FileHandler instance for reading files
        
    Returns:
        Selected file contents if any
    """
    if not file_paths:
        st.info("No files to display")
        return None
        
    # Create file selector
    file_options = [path for _, path in file_paths]
    selected_path = st.selectbox(
        "Select a file to view",
        file_options,
        format_func=lambda x: x.split('/')[-1]
    )
    
    if selected_path:
        content = file_handler.read_file(selected_path)
        if content:
            st.code(content, language=_get_language(selected_path))
            return content
    
    return None

def _get_language(filename: str) -> str:
    """Determine the programming language based on file extension."""
    ext = filename.split('.')[-1].lower()
    language_map = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'javascript',
        'html': 'html',
        'css': 'css',
        'md': 'markdown'
    }
    return language_map.get(ext, 'text') 