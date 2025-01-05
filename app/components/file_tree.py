import streamlit as st
from pathlib import Path

class FileTreeComponent:
    def __init__(self, file_tree):
        """Initialize the file tree component.
        
        Args:
            file_tree (dict): Dictionary representing the file tree structure
        """
        self.file_tree = file_tree
        
    def _render_tree_recursive(self, tree, path=""):
        """Recursively render the file tree structure.
        
        Args:
            tree (dict): Current subtree to render
            path (str): Current path in the tree
        
        Returns:
            str or None: Selected file path if a file is clicked, None otherwise
        """
        selected_file = None
        
        for name, item in sorted(tree.items()):
            current_path = str(Path(path) / name)
            
            if isinstance(item, dict):
                # Directory
                st.markdown(f"📁 **{name}**")
                with st.container():
                    st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;", unsafe_allow_html=True)
                    selected = self._render_tree_recursive(item, current_path)
                    if selected:
                        selected_file = selected
            else:
                # File
                if st.button(f"📄 {name}", key=current_path):
                    selected_file = current_path
        
        return selected_file
    
    def render(self):
        """Render the file tree component.
        
        Returns:
            str or None: Selected file path if a file is clicked, None otherwise
        """
        st.markdown("### Repository Structure")
        return self._render_tree_recursive(self.file_tree) 