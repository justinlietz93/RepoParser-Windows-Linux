import logging
import streamlit as st
from pathlib import Path
import yaml
from frontend.components.sidebar import SidebarComponent

logger = logging.getLogger(__name__)

def save_config_to_file(config_data):
    """
    Safely persist config changes to config/config.yaml.
    """
    try:
        import os
        from pathlib import Path

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
            file_tree: The dictionary returned by the crawler, containing:
                {
                  "path": <root_path_str>,
                  "contents": { ...nested directories and files... }
                }
        """
        # Initialize required session state
        if "config" not in st.session_state:
            st.session_state.config = {
                'ignore_patterns': {
                    'directories': [],
                    'files': []
                }
            }

        self.file_tree = file_tree
        self.root_path = Path(file_tree.get("path", "."))

        # Initialize all required state in a single dictionary
        if "ignore_tree_state" not in st.session_state:
            st.session_state["ignore_tree_state"] = {
                "expanded_dirs": set(),     # which directories are expanded
                "search_query": "",         # current search text
            }

        self.state = st.session_state["ignore_tree_state"]  # easy shorthand

    def render(self):
        """
        Main render function for the ignore tree UI.
        1) Renders the search box
        2) Renders the recursive tree structure
        3) Allows toggling expansion and ignore/unignore
        """
        st.subheader("Ignore Tree")

        # 1. SEARCH BAR
        # If user changes this, the page reruns automatically. We keep the new value in state.
        new_query = st.text_input(
            "Search",
            value=self.state["search_query"],
            placeholder="Type to filter files/directories...",
        )
        if new_query != self.state["search_query"]:
            self.state["search_query"] = new_query

        # 2. RENDER THE TREE ROOT
        # The crawler file_tree has a 'contents' key that is the top-level dict
        # representing subdirectories/files. We'll recursively walk that.
        contents = self.file_tree.get("contents", {})
        self.render_directory_contents(self.root_path, contents, level=0)

    def render_directory_contents(self, current_path: Path, directory_dict: dict, level: int):
        """
        Recursively render the given directory contents.

        Args:
            current_path: Path object representing the directory we are rendering
            directory_dict: The dict of {name: <subdir_dict or None if file>}
            level: used for indentation
        """
        # Sort everything by name so directories appear consistently
        # inside directories. We want directories first, files second.
        entries = sorted(directory_dict.items(), key=lambda x: x[0].lower())

        for name, subtree in entries:
            full_path = current_path / name
            rel_path = str(full_path.relative_to(self.root_path))
            is_directory = isinstance(subtree, dict)
            # Check search filter
            if not self._search_matches(rel_path):
                continue

            # Layout: [toggle icon col] [name col] [ignore button col]
            cols = st.columns([0.1, 0.7, 0.2])
            indent_str = "    " * level  # Basic indentation

            # A) Directory or File Icon
            if is_directory:
                expanded = rel_path in self.state["expanded_dirs"]
                toggle_label = "▼" if expanded else "▶"

                with cols[0]:
                    # Directory expand/collapse button
                    if st.button(
                        toggle_label,
                        key=f"expand_dir_{rel_path}",
                        help="Expand/Collapse directory",
                    ):
                        self._toggle_directory(rel_path)  # modifies expanded_dirs
            else:
                with cols[0]:
                    # Just an empty area or an icon
                    st.markdown("📄")

            # B) Path Text
            with cols[1]:
                display_name = f"{indent_str}{name}"
                if is_directory:
                    display_name = f"{indent_str}📁 {name}/"
                st.text(display_name)

            # C) Ignore Toggle
            with cols[2]:
                # Check if path is currently ignored
                ignored = self._is_path_ignored(full_path)
                toggle_symbol = "✓" if ignored else "×"
                toggle_help = "Currently ignored" if ignored else "Not ignored"

                if st.button(
                    toggle_symbol,
                    key=f"ignore_toggle_{rel_path}",
                    help=f"Toggle ignore on {rel_path} ({toggle_help})",
                ):
                    # Toggling ignore modifies config
                    self._toggle_ignore(full_path)

            # D) If directory is expanded, render children
            if is_directory and (rel_path in self.state["expanded_dirs"]):
                # subtree is a dict representing the child contents
                self.render_directory_contents(full_path, subtree, level + 1)

    def _toggle_directory(self, rel_path: str):
        """
        Add/remove rel_path in the expanded_dirs set to expand/collapse a directory.
        """
        expanded_dirs = self.state["expanded_dirs"]
        if rel_path in expanded_dirs:
            expanded_dirs.remove(rel_path)
        else:
            expanded_dirs.add(rel_path)

    def _search_matches(self, rel_path: str) -> bool:
        """
        Return True if rel_path matches current search query or if search is empty.
        """
        query = self.state["search_query"].strip().lower()
        if not query:
            return True
        return (query in rel_path.lower())

    def _is_path_ignored(self, path_obj: Path) -> bool:
        """
        Check if a path is currently ignored. If it's a directory,
        see if it's in the directory ignore list; if it's a file, check file ignore list.
        Also, check if any parent directory is ignored.
        """
        try:
            config = st.session_state.config
            patterns = config.get("ignore_patterns", {})
            rel_path = str(path_obj.relative_to(self.root_path))

            if path_obj.is_dir():
                # Check direct or parent ignore
                if rel_path in patterns.get("directories", []):
                    return True
                # Or a parent path is in directories
                for parent in path_obj.parents:
                    if parent == self.root_path:
                        break
                    parent_rel = str(parent.relative_to(self.root_path))
                    if parent_rel in patterns.get("directories", []):
                        return True
            else:
                # File check
                if rel_path in patterns.get("files", []):
                    return True
                # Or a parent directory is ignored
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

    def _toggle_ignore(self, path_obj: Path):
        """
        Toggle a path (file or directory) into or out of st.session_state.config['ignore_patterns'].
        Then persist changes to config.yaml.
        """
        try:
            config = st.session_state.config
            patterns = config.setdefault("ignore_patterns", {"directories": [], "files": []})
            dirs = patterns.setdefault("directories", [])
            files = patterns.setdefault("files", [])

            # Convert path to rel_path for storing
            rel_path = str(path_obj.relative_to(self.root_path))
            if path_obj.is_dir():
                if rel_path in dirs:
                    dirs.remove(rel_path)
                    logger.info(f"Unignored directory: {rel_path}")
                else:
                    dirs.append(rel_path)
                    logger.info(f"Ignored directory: {rel_path}")
            else:
                if rel_path in files:
                    files.remove(rel_path)
                    logger.info(f"Unignored file: {rel_path}")
                else:
                    files.append(rel_path)
                    logger.info(f"Ignored file: {rel_path}")

            # Write updated config to file
            success = save_config_to_file(config)
            if success:
                st.session_state.config = config.copy()  # ensure state is updated
            else:
                st.error("Could not save updated ignore config.")

        except Exception as e:
            logger.exception(f"Error toggling ignore for path {path_obj}: {e}")
            st.error(f"Failed to toggle ignore: {str(e)}") 