import streamlit as st
from typing import Dict, List

def render_file_tree(tree_str: str) -> None:
    """
    Render the file tree structure.
    
    Args:
        tree_str: String representation of the directory tree
    """
    lines = tree_str.split('\n')
    
    # Create expandable sections for directories
    current_path: List[str] = []
    sections: Dict[str, List[str]] = {"": []}
    
    for line in lines:
        indent = len(line) - len(line.lstrip())
        depth = indent // 4
        
        # Adjust current path based on depth
        current_path = current_path[:depth]
        
        if "[" in line and "]" in line:
            # Directory
            dir_name = line.strip()[1:-2]  # Remove [ and /]
            current_path.append(dir_name)
            path_key = "/".join(current_path)
            sections[path_key] = []
        else:
            # File
            if current_path:
                path_key = "/".join(current_path)
                sections[path_key].append(line.strip())
            else:
                sections[""].append(line.strip())
    
    # Render tree with expandable sections
    for path, items in sections.items():
        if path:
            with st.expander(f"📁 {path.split('/')[-1]}"):
                for item in items:
                    st.text(f"📄 {item}")
        else:
            for item in items:
                if item:
                    st.text(f"📄 {item}") 