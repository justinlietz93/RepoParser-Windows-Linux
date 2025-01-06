# Repo_Crawler/frontend/components/ignore_tree.py

import logging
import re
import streamlit as st
from pathlib import Path
import yaml
from frontend.components.sidebar import SidebarComponent

logger = logging.getLogger(__name__)

def _sanitize_key(path_string: str) -> str:
    """
    Replace non-alphanumeric characters with underscores
    to ensure valid, stable widget keys.
    """
    return re.sub(r'[^a-zA-Z0-9_-]+', '_', path_string)

def save_config_to_file(config_data):
    """
    Safely persist config changes to config/config.yaml.
    """
    try:
        config_path = Path("config/config.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.exception("Error saving configuration")
        st.error(f"Failed to save ignore patterns: {str(e)}")
        return False

class IgnoreTreeComponent:
    def __init__(self, file_tree: dict):
        """
        Args:
            file_tree: {
                "path": <root_path_str>,
                "contents": {...}
            }
        """
        # Ensure essential session_state keys exist
        if "config" not in st.session_state:
            st.session_state.config = {
                'ignore_patterns': {
                    'directories': [],
                    'files': []
                }
            }
        if "loaded_rules" not in st.session_state:
            st.session_state.loaded_rules = {}  # prevent missing-key errors

        self.file_tree = file_tree
        self.root_path = Path(file_tree.get("path", "."))
        if "ignore_tree_state" not in st.session_state:
            st.session_state["ignore_tree_state"] = {
                "expanded_dirs": set(),
                "search_query": "",
            }
        self.state = st.session_state["ignore_tree_state"]

    def render(self):
        st.subheader("Ignore Tree")
        new_query = st.text_input(
            "Search",
            value=self.state["search_query"],
            placeholder="Type to filter files/directories...",
        )
        if new_query != self.state["search_query"]:
            self.state["search_query"] = new_query

        contents = self.file_tree.get("contents", {})
        self.render_directory_contents(self.root_path, contents, level=0)

    def render_directory_contents(self, current_path: Path, directory_dict: dict, level: int):
        entries = sorted(directory_dict.items(), key=lambda x: x[0].lower())
        for name, subtree in entries:
            full_path = current_path / name
            rel_path = str(full_path.relative_to(self.root_path))
            is_directory = isinstance(subtree, dict)
            if not self._search_matches(rel_path):
                continue

            cols = st.columns([0.1, 0.7, 0.2])
            indent_str = "    " * level
            expanded_key = _sanitize_key(f"expand_dir_{rel_path}")
            toggle_key = _sanitize_key(f"ignore_toggle_{rel_path}")

            if is_directory:
                expanded = rel_path in self.state["expanded_dirs"]
                toggle_label = "▼" if expanded else "▶"
                with cols[0]:
                    if st.button(
                        toggle_label,
                        key=expanded_key,
                        help="Expand/Collapse directory",
                    ):
                        self._toggle_directory(rel_path)
            else:
                with cols[0]:
                    st.markdown("📄")

            with cols[1]:
                display_name = f"{indent_str}📁 {name}/" if is_directory else f"{indent_str}{name}"
                st.text(display_name)

            with cols[2]:
                ignored = self._is_path_ignored(full_path)
                toggle_symbol = "✓" if ignored else "×"
                toggle_help = "Currently ignored" if ignored else "Not ignored"
                if st.button(
                    toggle_symbol,
                    key=toggle_key,
                    help=f"Toggle ignore on {rel_path} ({toggle_help})",
                ):
                    # Call the method within the class now
                    self._toggle_ignore(full_path)

            if is_directory and (rel_path in self.state["expanded_dirs"]):
                self.render_directory_contents(full_path, subtree, level + 1)

    def _toggle_directory(self, rel_path: str):
        if rel_path in self.state["expanded_dirs"]:
            self.state["expanded_dirs"].remove(rel_path)
        else:
            self.state["expanded_dirs"].add(rel_path)

    def _toggle_ignore(self, path_obj: Path):
        """
        Now a method inside IgnoreTreeComponent,
        fixing the AttributeError and persisting ignore patterns.
        """
        try:
            config = st.session_state.config
            patterns = config.setdefault("ignore_patterns", {"directories": [], "files": []})
            dirs = patterns.setdefault("directories", [])
            files = patterns.setdefault("files", [])
            rel_path = str(path_obj.relative_to(self.root_path))

            if path_obj.is_dir():
                if rel_path in dirs:
                    dirs.remove(rel_path)
                else:
                    dirs.append(rel_path)
            else:
                if rel_path in files:
                    files.remove(rel_path)
                else:
                    files.append(rel_path)

            # Persist changes in Streamlit session and config file
            success = save_config_to_file(config)
            if success:
                st.session_state.config = config.copy()
            else:
                st.error("Could not save updated ignore config.")
        except Exception as e:
            logger.exception(f"Error toggling ignore for path {path_obj}: {e}")
            st.error(f"Failed to toggle ignore: {str(e)}")

    def _search_matches(self, rel_path: str) -> bool:
        query = self.state["search_query"].strip().lower()
        if not query:
            return True
        return (query in rel_path.lower())

    def _is_path_ignored(self, path_obj: Path) -> bool:
        try:
            config = st.session_state.config
            patterns = config.get("ignore_patterns", {})
            rel_path = str(path_obj.relative_to(self.root_path))

            if path_obj.is_dir():
                if rel_path in patterns.get("directories", []):
                    return True
                for parent in path_obj.parents:
                    if parent == self.root_path:
                        break
                    parent_rel = str(parent.relative_to(self.root_path))
                    if parent_rel in patterns.get("directories", []):
                        return True
            else:
                if rel_path in patterns.get("files", []):
                    return True
                for parent in path_obj.parents:
                    if parent == self.root_path:
                        break
                    parent_rel = str(parent.relative_to(self.root_path))
                    if parent_rel in patterns.get("directories", []):
                        return True
            return False
        except Exception as e:
            logger.exception(f"Error checking if path is ignored: {path_obj} | {e}")
            return False
