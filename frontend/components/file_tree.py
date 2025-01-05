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
        if 'selected_node' not in st.session_state:
            st.session_state.selected_node = None
        if 'expanded_nodes' not in st.session_state:
            st.session_state.expanded_nodes = set()

    def render_tree_node(self, path: Path, level: int = 0):
        """Render a tree node and its children using checkboxes."""
        try:
            # Sort items: directories first, then files
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                indent = "│   " * level
                is_dir = item.is_dir()
                
                # Create a row for each item
                cols = st.columns([0.05, 0.85, 0.1])
                
                if is_dir:
                    # Directory node with inline checkbox
                    with cols[0]:
                        is_expanded = st.checkbox(
                            label=f"Toggle {item.name}",
                            key=f"dir_{item}",
                            value=str(item) in st.session_state.expanded_nodes,
                            label_visibility="collapsed"
                        )
                        
                        if is_expanded and str(item) not in st.session_state.expanded_nodes:
                            st.session_state.expanded_nodes.add(str(item))
                        elif not is_expanded and str(item) in st.session_state.expanded_nodes:
                            st.session_state.expanded_nodes.remove(str(item))
                    
                    with cols[1]:
                        prefix = "└── " if level > 0 else ""
                        st.markdown(f"{indent}{prefix}📁 {item.name}/", unsafe_allow_html=True)
                    
                    # Render children if expanded
                    if is_expanded:
                        self.render_tree_node(item, level + 1)
                else:
                    # File node with select button
                    with cols[1]:
                        prefix = "└── " if level > 0 else ""
                        st.markdown(f"{indent}{prefix}📄 {item.name}", unsafe_allow_html=True)
                    with cols[2]:
                        if st.button(
                            "📋",
                            key=f"select_{item}",
                            help=f"Select {item.name}",
                            use_container_width=True
                        ):
                            st.session_state.selected_node = str(item)
                            return str(item)
                            
        except Exception as e:
            logger.error(f"Error processing {path}: {str(e)}")
            st.error(f"Error accessing {path}")
            return None

    def render(self):
        """Render the file tree."""
        st.markdown("### Repository Structure")
        
        try:
            # Create a container for the tree
            tree_container = st.container()
            with tree_container:
                selected_file = self.render_tree_node(self.root_path)
                if selected_file and selected_file != st.session_state.selected_node:
                    st.session_state.selected_node = selected_file
            
            return st.session_state.selected_node
            
        except Exception as e:
            logger.error(f"Error rendering file tree: {str(e)}")
            st.error(f"Error rendering file tree: {str(e)}")
            return None 