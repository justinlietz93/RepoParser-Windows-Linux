# Repo_Crawler/frontend/components/file_tree.py

import streamlit as st
from pathlib import Path
import logging
import re
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)

def _sanitize_key(path_string: str) -> str:
    """
    Replace all non-alphanumeric characters with underscores
    to ensure a valid, stable Streamlit widget key.
    """
    return re.sub(r'[^a-zA-Z0-9_-]+', '_', path_string)

class FileTreeComponent:
    def __init__(self, file_tree: Dict[str, Any]):
        self.root_path = Path(file_tree['path'])
        self.initialize_state()
        if 'current_tree' not in st.session_state:
            st.session_state.current_tree = file_tree
        elif file_tree != st.session_state.current_tree:
            st.session_state.expanded_dirs.clear()
            st.session_state.current_tree = file_tree

    def initialize_state(self):
        required_state = {
            'expanded_dirs': set(),
            'selected_file': None,
            'search_query': "",
            'file_tree_key': 0,
        }
        for key, default_value in required_state.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def toggle_directory(self, dir_path: str):
        if dir_path in st.session_state.expanded_dirs:
            st.session_state.expanded_dirs.remove(dir_path)
        else:
            st.session_state.expanded_dirs.add(dir_path)

    def matches_search(self, path: Path) -> bool:
        query = st.session_state.search_query.lower()
        return (not query) or (query in path.name.lower())

    def render_tree_node(self, path: Path, level: int = 0) -> Optional[str]:
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            if st.session_state.search_query:
                filtered = []
                for item in items:
                    if item.is_dir():
                        if any(self.matches_search(child) for child in item.rglob("*")) or self.matches_search(item):
                            filtered.append(item)
                    else:
                        if self.matches_search(item):
                            filtered.append(item)
                items = filtered

            for item in items:
                item_key_raw = str(item.resolve())
                item_key = _sanitize_key(item_key_raw)  # Clean up the path for the widget key
                is_dir = item.is_dir()
                cols = st.columns([0.05, 0.85, 0.1])

                if is_dir:
                    expanded_widget_key = f"expand_{item_key}"

                    with cols[0]:
                        # Retrieve the default state from expanded_dirs
                        default_expanded = (item_key_raw in st.session_state.expanded_dirs)
                        # Only read the widget's value, do not overwrite st.session_state for the same key
                        toggled = st.checkbox(
                            "Toggle directory",
                            key=expanded_widget_key,
                            value=default_expanded,
                            label_visibility="collapsed"
                        )
                        # If widget changed, reflect it in expanded_dirs
                        if toggled and item_key_raw not in st.session_state.expanded_dirs:
                            st.session_state.expanded_dirs.add(item_key_raw)
                        elif not toggled and item_key_raw in st.session_state.expanded_dirs:
                            st.session_state.expanded_dirs.remove(item_key_raw)

                    with cols[1]:
                        indent = "│   " * level
                        prefix = "└── " if level > 0 else ""
                        st.markdown(f"{indent}{prefix}📁 {item.name}/", help=f"Directory: {item_key_raw}")

                    if item_key_raw in st.session_state.expanded_dirs:
                        selected = self.render_tree_node(item, level + 1)
                        if selected:
                            return selected
                else:
                    with cols[1]:
                        indent = "│   " * level
                        prefix = "└── " if level > 0 else ""
                        st.markdown(f"{indent}{prefix}📄 {item.name}", help=f"File: {item_key_raw}")

                    with cols[2]:
                        select_widget_key = f"select_{item_key}"
                        if st.button("📋", key=select_widget_key, help=f"Select {item.name}", use_container_width=True):
                            st.session_state.selected_file = item_key_raw
                            return item_key_raw

        except Exception as e:
            logger.error(f"Error processing {path}: {str(e)}")
            st.error(f"Error accessing {path}")
            return None
        return None

    def render(self) -> Optional[str]:
        try:
            with st.container():
                st.markdown("## File Tree")
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

                cols = st.columns([0.05, 0.85, 0.1])
                with cols[0]:
                    st.write("")
                with cols[1]:
                    if st.button("🔄 Refresh", key=f"refresh_tree_{st.session_state.file_tree_key}", help="Refresh file tree"):
                        st.session_state.expanded_dirs.clear()
                        st.session_state.selected_file = None
                        st.session_state.search_query = ""
                        st.session_state.file_tree_key += 1
                        st.rerun()

                selected_file = self.render_tree_node(self.root_path)
                if selected_file and selected_file != st.session_state.selected_file:
                    st.session_state.selected_file = selected_file
                return st.session_state.selected_file

        except Exception as e:
            logger.error(f"Error rendering file tree: {str(e)}")
            st.error(f"Error rendering file tree: {str(e)}")
            return None
