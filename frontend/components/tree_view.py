import logging
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import json
from typing import Dict, Set, Tuple, Any

# Configure logger
logger = logging.getLogger(__name__)

class TreeView:
    def __init__(self):
        self.html_template = '''
        <style>
            .vscode-tree {{
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                background: transparent;
                color: #e0e0e0;
                padding: 4px;
                height: 100%;
                overflow-y: auto;
                overflow-x: hidden;
                width: 100%;
                box-sizing: border-box;
            }}
            .vscode-tree ul {{
                list-style: none;
                padding-left: 0;
                margin: 0;
            }}
            .vscode-tree li {{
                white-space: nowrap;
                cursor: pointer;
                line-height: 20px;
                width: 100%;
            }}
            .vscode-tree li > div {{
                display: flex;
                align-items: center;
                padding: 0 4px;
                border-radius: 3px;
            }}
            .vscode-tree li > div:hover {{
                background: rgba(255,255,255,0.1);
            }}
            .vscode-tree .indent {{
                display: inline-block;
                width: 12px;
                height: 100%;
                position: relative;
            }}
            .vscode-tree .indent::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 5px;
                bottom: 0;
                width: 1px;
                background: rgba(255,255,255,0.1);
            }}
            .vscode-tree li:last-child > .indent::before {{
                height: 11px;
            }}
            .vscode-tree .arrow {{
                width: 14px;
                height: 14px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-right: 2px;
                color: #808080;
                font-size: 8px;
                transform: rotate(0deg);
                transition: transform 0.15s;
            }}
            .vscode-tree .arrow.expanded {{
                transform: rotate(90deg);
            }}
            .vscode-tree .arrow.hidden {{
                visibility: hidden;
            }}
            .vscode-tree .icon {{
                width: 16px;
                height: 16px;
                margin-right: 4px;
                opacity: 0.8;
                font-size: 12px;
            }}
            .vscode-tree .folder {{
                color: #dcb67a;
            }}
            .vscode-tree .file {{
                color: #8a9199;
            }}
            .vscode-tree .name {{
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                padding-right: 4px;
                font-size: 12px;
            }}
            .vscode-tree input[type="checkbox"] {{
                margin: 0 4px 0 0;
                padding: 0;
                opacity: 0.8;
                cursor: pointer;
                width: 13px;
                height: 13px;
            }}
            .vscode-tree input[type="checkbox"]:hover {{
                opacity: 1;
            }}
            .vscode-tree .checkbox-wrapper {{
                display: flex;
                align-items: center;
                flex: 1;
                min-width: 0;
            }}
            .vscode-tree .collapsed > ul {{
                display: none;
            }}
        </style>
        
        <div class="vscode-tree">
            {tree_html}
        </div>
        
        <script>
            document.querySelectorAll('.vscode-tree li').forEach(item => {{
                const arrow = item.querySelector('.arrow');
                if (arrow && !arrow.classList.contains('hidden')) {{
                    item.addEventListener('click', (e) => {{
                        if (e.target.type !== 'checkbox') {{
                            item.classList.toggle('collapsed');
                            arrow.classList.toggle('expanded');
                        }}
                    }});
                }}
            }});

            document.querySelectorAll('.vscode-tree input[type="checkbox"]').forEach(checkbox => {{
                checkbox.addEventListener('change', (e) => {{
                    e.stopPropagation();
                    const data = {{
                        path: e.target.getAttribute('data-path'),
                        type: e.target.getAttribute('data-type'),
                        checked: e.target.checked
                    }};
                    window.parent.postMessage({{type: 'tree_toggle', data: data}}, '*');
                }});
            }});
        </script>
        '''
        
    def _get_file_icon(self, name: str) -> str:
        """Get appropriate icon based on file extension."""
        ext = Path(name).suffix.lower()
        icons = {
            '.py': '📜',    # Python files
            '.md': '📝',    # Markdown
            '.json': '📋',  # JSON
            '.yaml': '⚙️',  # YAML/Config
            '.yml': '⚙️',
            '.txt': '📄',   # Text
            '.css': '🎨',   # Styles
            '.html': '🌐',  # Web
            '.js': '📦',    # JavaScript
            '.ts': '📦',    # TypeScript
            '.jsx': '⚛️',   # React
            '.tsx': '⚛️',
            '.vue': '🎯',   # Vue
            '.rs': '🦀',    # Rust
            '.go': '🐹',    # Go
            '.java': '☕',  # Java
            '.cpp': '⚡',   # C++
            '.h': '⚡',
            '.cs': '🔷',    # C#
            '.rb': '💎',    # Ruby
            '.php': '🐘',   # PHP
            '.swift': '🍎',  # Swift
            '.kt': '🎯',    # Kotlin
            '.r': '📊',     # R
            '.sql': '🗃️',   # SQL
            '.sh': '💻',    # Shell
            '.bat': '💻',   # Batch
            '.ps1': '💻',   # PowerShell
            '.env': '🔒',   # Environment
            '.gitignore': '👁️',  # Git
            '.dockerignore': '🐳',
            'dockerfile': '🐳',  # Docker
            '.cursorrules': '🎮'  # Custom rules
        }
        return icons.get(ext, '📄')
        
    def _build_tree_html(self, tree, current_path="", ignored_dirs=None, ignored_files=None, depth=0):
        try:
            if ignored_dirs is None:
                ignored_dirs = set()
            if ignored_files is None:
                ignored_files = set()
                
            html_parts = ['<ul>']
            
            for name, content in sorted(tree.items()):
                if name.startswith('__'):  # Skip error entries
                    continue
                    
                path = str(Path(current_path) / name)
                indentation = '<span class="indent"></span>' * depth
                
                try:
                    if content is None:  # File
                        is_ignored = path in ignored_files
                        icon = self._get_file_icon(name)
                        file_html = (
                            '<li>'
                            '<div>'
                            '{indent}'
                            '<span class="arrow hidden">▶</span>'
                            '<div class="checkbox-wrapper">'
                            '<input type="checkbox" data-path="{path}" data-type="file" {checked}>'
                            '<span class="icon file">{icon}</span>'
                            '<span class="name">{name}</span>'
                            '</div>'
                            '</div>'
                            '</li>'
                        ).format(
                            indent=indentation,
                            path=path,
                            checked='checked' if not is_ignored else '',
                            icon=icon,
                            name=name
                        )
                        html_parts.append(file_html)
                    else:  # Directory
                        is_ignored = path in ignored_dirs
                        dir_html = (
                            '<li>'
                            '<div>'
                            '{indent}'
                            '<span class="arrow">▶</span>'
                            '<div class="checkbox-wrapper">'
                            '<input type="checkbox" data-path="{path}" data-type="dir" {checked}>'
                            '<span class="icon folder">📁</span>'
                            '<span class="name">{name}/</span>'
                            '</div>'
                            '</div>'
                            '{children}'
                            '</li>'
                        ).format(
                            indent=indentation,
                            path=path,
                            checked='checked' if not is_ignored else '',
                            name=name,
                            children=self._build_tree_html(content, path, ignored_dirs, ignored_files, depth + 1)
                        )
                        html_parts.append(dir_html)
                except Exception as e:
                    logger.error(f"Error processing tree item {name}: {str(e)}")
                    continue
            
            html_parts.append('</ul>')
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error building tree HTML: {str(e)}")
            return '<ul><li>Error building tree</li></ul>'

    def render(self, tree: Dict[str, Any], ignored_dirs: Set[str] = None, ignored_files: Set[str] = None) -> Tuple[Set[str], Set[str]]:
        """Render a VS Code-style tree view."""
        try:
            # Generate a stable key for this tree instance
            tree_key = f"tree_view_{hash(str(tree))}"
            
            tree_html = self._build_tree_html(
                tree, 
                ignored_dirs=ignored_dirs, 
                ignored_files=ignored_files
            )
            
            # Inject the tree HTML into the template
            html = self.html_template.format(tree_html=tree_html)
            
            # Render the HTML
            components.html(html, height=400, scrolling=True)
            
            # Initialize or update session state
            if tree_key not in st.session_state:
                st.session_state[tree_key] = {
                    'ignored_dirs': set(ignored_dirs or []),
                    'ignored_files': set(ignored_files or [])
                }
                
            return st.session_state[tree_key]['ignored_dirs'], st.session_state[tree_key]['ignored_files']
            
        except Exception as e:
            logger.error(f"Error rendering tree view: {str(e)}", exc_info=True)
            st.error("Failed to render file tree. Please check the logs for details.")
            return ignored_dirs or set(), ignored_files or set() 