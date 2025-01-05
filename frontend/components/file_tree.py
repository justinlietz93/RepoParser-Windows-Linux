import streamlit as st
from pathlib import Path
import logging
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)

class FileTreeComponent:
    def __init__(self, file_tree: Dict[str, Any]):
        """Initialize the file tree component.
        
        Args:
            file_tree (Dict[str, Any]): Dictionary containing file tree information
                with at least a 'path' key pointing to the root directory.
        """
        self.root_path = Path(file_tree['path'])
        self.initialize_state()
        # Store file tree in session state to detect changes
        if 'current_tree' not in st.session_state:
            st.session_state.current_tree = file_tree
        elif file_tree != st.session_state.current_tree:
            # Tree has changed, reset expansion state
            st.session_state.expanded_dirs = set()
            st.session_state.current_tree = file_tree

    def initialize_state(self):
        """Initialize session state for tree expansion and selection."""
        if 'expanded_dirs' not in st.session_state:
            st.session_state.expanded_dirs = set()
        if 'selected_file' not in st.session_state:
            st.session_state.selected_file = None
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
            
    def toggle_directory(self, dir_path: str):
        """Toggle directory expansion state.
        
        Args:
            dir_path (str): Path to the directory to toggle
        """
        if dir_path in st.session_state.expanded_dirs:
            st.session_state.expanded_dirs.remove(dir_path)
        else:
            st.session_state.expanded_dirs.add(dir_path)
    
    def matches_search(self, path: Path) -> bool:
        """Check if path matches current search query."""
        if not st.session_state.search_query:
            return True
        query = st.session_state.search_query.lower()
        return query in path.name.lower()
    
    def render_tree_node(self, path: Path, level: int = 0) -> Optional[str]:
        """Recursively render a tree node and its children.
        
        Args:
            path (Path): Current path to render
            level (int): Current nesting level for indentation
            
        Returns:
            Optional[str]: Selected file path if a file is selected, None otherwise
        """
        try:
            # Sort items: directories first, then files
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            # Filter items based on search
            if st.session_state.search_query:
                matching_items = []
                for item in items:
                    if item.is_dir():
                        has_matches = any(
                            self.matches_search(child) 
                            for child in item.rglob("*")
                        )
                        if has_matches or self.matches_search(item):
                            matching_items.append(item)
                    elif self.matches_search(item):
                        matching_items.append(item)
                items = matching_items
            
            for item in items:
                # Create unique key for this item
                item_key = str(item.resolve())
                is_dir = item.is_dir()
                
                # Create a row with proper spacing
                cols = st.columns([0.05, 0.85, 0.1])
                
                if is_dir:
                    # Directory node with toggle
                    with cols[0]:
                        is_expanded = st.checkbox(
                            "Toggle directory",
                            key=f"dir_{item_key}",
                            value=item_key in st.session_state.expanded_dirs,
                            label_visibility="collapsed",
                            on_change=self.toggle_directory,
                            args=(item_key,)
                        )
                    
                    with cols[1]:
                        indent = "│   " * level
                        prefix = "└── " if level > 0 else ""
                        st.markdown(
                            f"{indent}{prefix}📁 {item.name}/",
                            help=f"Directory: {item_key}"
                        )
                    
                    # Render children if expanded
                    if is_expanded:
                        selected = self.render_tree_node(item, level + 1)
                        if selected:
                            return selected
                else:
                    # File node with select button
                    with cols[1]:
                        indent = "│   " * level
                        prefix = "└── " if level > 0 else ""
                        st.markdown(
                            f"{indent}{prefix}📄 {item.name}",
                            help=f"File: {item_key}"
                        )
                    
                    with cols[2]:
                        if st.button(
                            "📋",
                            key=f"select_{item_key}",
                            help=f"Select {item.name}",
                            use_container_width=True
                        ):
                            st.session_state.selected_file = item_key
                            return item_key
                            
        except Exception as e:
            logger.error(f"Error processing {path}: {str(e)}")
            st.error(f"Error accessing {path}")
            return None
            
        return None

    def render(self) -> Optional[str]:
        """Render the complete file tree.
        
        Returns:
            Optional[str]: Selected file path if a file is selected, None otherwise
        """
        
        try:
            # Initialize or increment refresh key
            if 'file_tree_key' not in st.session_state:
                st.session_state.file_tree_key = 0
            
            # Create a container for better organization
            with st.container():
                # Add header
                st.markdown("## File Tree")
                
                # Add search bar
                search = st.text_input(
                    "🔍",
                    value=st.session_state.search_query,
                    placeholder="Search files (ex. 'main.py' case insensitive)",
                    label_visibility="collapsed",
                    key=f"search_{st.session_state.file_tree_key}"
                )
                if search != st.session_state.search_query:
                    st.session_state.search_query = search
                    st.rerun()
                
                # Create first tree row with refresh button
                cols = st.columns([0.05, 0.85, 0.1])
                with cols[0]:
                    st.write("")  # Empty space for alignment
                with cols[1]:
                    if st.button("🔄 Refresh", key=f"refresh_tree_{st.session_state.file_tree_key}", help="Refresh file tree"):
                        st.session_state.expanded_dirs = set()
                        st.session_state.selected_file = None
                        st.session_state.search_query = ""
                        st.session_state.file_tree_key += 1
                        st.rerun()
                
                # Render the tree
                selected_file = self.render_tree_node(self.root_path)
                
                # Update selection state if needed
                if selected_file and selected_file != st.session_state.selected_file:
                    st.session_state.selected_file = selected_file
                
                return st.session_state.selected_file
                    
        except Exception as e:
            logger.error(f"Error rendering file tree: {str(e)}")
            st.error(f"Error rendering file tree: {str(e)}")
            return None 