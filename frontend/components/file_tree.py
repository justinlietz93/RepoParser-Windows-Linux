import streamlit as st
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileTreeComponent:
    def __init__(self, file_tree):
        """Initialize the file tree component."""
        self.root_path = Path(file_tree['path'])
        self.initialize_state()
    
    def initialize_state(self):
        """Initialize session state for tree expansion state."""
        if 'tree_state' not in st.session_state:
            st.session_state.tree_state = {}
    
    def toggle_dir(self, path):
        """Toggle directory expansion state."""
        if path not in st.session_state.tree_state:
            st.session_state.tree_state[path] = True  # Expanded by default
        else:
            st.session_state.tree_state[path] = not st.session_state.tree_state[path]
    
    def is_expanded(self, path):
        """Check if directory is expanded."""
        return st.session_state.tree_state.get(path, True)
    
    def render_tree_node(self, path, name, is_dir, level=0):
        """Render a single tree node (file or directory)."""
        indent = "    " * level
        
        if is_dir:
            # Directory node
            col1, col2 = st.columns([20, 1])
            with col1:
                expanded = self.is_expanded(str(path))
                icon = "📂 " if expanded else "📁 "
                if st.button(f"{indent}{icon}{name}/", key=f"dir_{path}"):
                    self.toggle_dir(str(path))
                
                if expanded:
                    try:
                        # Sort directories first, then files
                        items = sorted(path.iterdir(), 
                                    key=lambda x: (not x.is_dir(), x.name.lower()))
                        for item in items:
                            self.render_tree_node(
                                item,
                                item.name,
                                item.is_dir(),
                                level + 1
                            )
                    except Exception as e:
                        logger.error(f"Error reading directory {path}: {str(e)}")
                        st.error(f"Error reading directory: {str(e)}")
        else:
            # File node
            col1, col2 = st.columns([20, 1])
            with col1:
                if st.button(f"{indent}📄 {name}", key=f"file_{path}"):
                    return str(path)
        
        return None
    
    def render(self):
        """Render the entire file tree."""
        st.markdown("### Repository Structure")
        
        selected_file = None
        
        try:
            # Sort directories first, then files
            items = sorted(self.root_path.iterdir(), 
                         key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                result = self.render_tree_node(item, item.name, item.is_dir())
                if result:
                    selected_file = result
        
        except Exception as e:
            logger.error(f"Error rendering file tree: {str(e)}")
            st.error(f"Error rendering file tree: {str(e)}")
        
        return selected_file 