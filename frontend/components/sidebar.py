import streamlit as st
import yaml
from pathlib import Path
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SidebarComponent:
    def __init__(self):
        """Initialize the sidebar component."""
        self.default_config = {
            'local_root': '',
            'ignore_patterns': {
                'directories': [
                    '.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.env',
                    'build', 'dist', '.idea', '.vscode', '.vs', 'bin', 'obj', 'out', 'target',
                    'coverage', '.coverage', '.pytest_cache', '.mypy_cache', '.tox', '.eggs',
                    '.sass-cache', 'bower_components', 'jspm_packages', '.next', '.nuxt',
                    '.serverless', '.terraform', 'vendor'
                ],
                'files': [
                    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib', '*.egg',
                    '*.egg-info', '*.whl', '.DS_Store', '.env', '*.log', '*.swp', '*.swo',
                    '*.class', '*.jar', '*.war', '*.nar', '*.ear', '*.zip', '*.tar.gz',
                    '*.rar', '*.min.js', '*.min.css', '*.map', '.env.local',
                    '.env.development.local', '.env.test.local', '.env.production.local',
                    '.env.*', '*.sqlite', '*.db', '*.db-shm', '*.db-wal', '*.suo',
                    '*.user', '*.userosscache', '*.sln.docstates', 'thumbs.db', '*.cache',
                    '*.bak', '*.tmp', '*.temp', '*.pid', '*.seed', '*.pid.lock',
                    '*.tsbuildinfo', '.eslintcache', '.node_repl_history', '.yarn-integrity',
                    '.grunt', '.lock-wscript'
                ]
            },
            'model': 'gpt-4'
        }
        self.initialize_state()
        
    def initialize_state(self):
        """Initialize session state for sidebar."""
        if 'config' not in st.session_state:
            st.session_state.config = self.default_config.copy()
            self.save_config(self.default_config)
        if 'loaded_config' not in st.session_state:
            st.session_state.loaded_config = None
        if 'loaded_rules' not in st.session_state:
            st.session_state.loaded_rules = {}
    
    def save_config(self, config_data: Dict[str, Any]):
        """Save configuration to config.yaml."""
        try:
            config_path = Path('config/config.yaml')
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Update session state, ensuring default values are preserved
            new_config = self.default_config.copy()
            new_config.update(config_data)
            st.session_state.config = new_config
            
            # Save to file
            with open(config_path, 'w') as f:
                yaml.dump(st.session_state.config, f, default_flow_style=False)
            
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            st.error("Failed to save configuration")
            return False
    
    def load_config_file(self, uploaded_file) -> bool:
        """Load configuration from uploaded file."""
        try:
            # Read and parse YAML content
            content = uploaded_file.getvalue().decode()
            config_data = yaml.safe_load(content)
            
            # Validate config structure
            required_keys = {'local_root', 'ignore_patterns', 'model'}
            if not all(key in config_data for key in required_keys):
                st.error("Invalid configuration file format")
                return False
            
            # Save the configuration, which will merge with defaults
            return self.save_config(config_data)
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error(f"Error loading configuration: {str(e)}")
            return False
    
    def clear_state(self):
        """Clear all sidebar-related state."""
        st.session_state.config = self.default_config.copy()
        st.session_state.loaded_config = None
        st.session_state.loaded_rules = {}
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
        self.save_config(self.default_config)
    
    def render(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("Repository Crawler 🔍")
            
            # Create tabs for different settings
            settings_tab, files_tab, patterns_tab = st.tabs(["Settings", "Files", "Patterns"])
            
            # Settings tab - contains model and repository settings
            with settings_tab:
                # Model selection
                st.markdown("### Model Settings")
                model = st.selectbox(
                    "Token Analysis Model",
                    options=["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                    index=["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"].index(
                        st.session_state.config.get('model', 'gpt-4')
                    ),
                    help="Select the model to use for token analysis"
                )
                if model != st.session_state.config.get('model', 'gpt-4'):
                    st.session_state.config['model'] = model
                    self.save_config({'model': model})
                
                # Repository path
                st.markdown("### Repository")
                repo_path = st.text_input(
                    "Path",
                    value=st.session_state.config.get('local_root', ''),
                    help="Enter the full path to your local repository",
                    placeholder="C:/path/to/repository"
                )
                
                if st.button("📂 Browse for Repository", help="Browse for repository directory", use_container_width=True):
                    # Use system file dialog
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    root.attributes('-topmost', True)  # Bring dialog to front
                    selected_path = filedialog.askdirectory()
                    root.destroy()
                    
                    if selected_path:
                        # Convert to Windows path format
                        repo_path = str(Path(selected_path))
                        st.session_state.config['local_root'] = repo_path
                        self.save_config({'local_root': repo_path})
                        st.rerun()
                
                if repo_path != st.session_state.config.get('local_root', ''):
                    st.session_state.config['local_root'] = repo_path
                    self.save_config({'local_root': repo_path})
            
            # Files tab - contains file uploads and management
            with files_tab:
                if 'loaded_config' not in st.session_state:
                    st.session_state.loaded_config = None
                if 'loaded_rules' not in st.session_state:
                    st.session_state.loaded_rules = {}
                
                # Show loaded rule files first
                if st.session_state.loaded_rules:
                    st.markdown("### Loaded Rule Files")
                    # Convert to list to avoid modification during iteration
                    for filename in list(st.session_state.loaded_rules.keys()):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"- {filename}")
                        with col2:
                            if st.button("❌", key=f"remove_rule_{filename}", help=f"Remove {filename}"):
                                del st.session_state.loaded_rules[filename]
                                st.rerun()
                
                # Show config status and clear button
                if st.session_state.loaded_config:
                    st.success(f"Using config: {st.session_state.loaded_config}")
                    if st.button("❌ Clear All", key="clear_all_config"):
                        self.clear_state()
                        st.rerun()
                
                # File uploader
                st.markdown("### Upload Files")
                uploaded_files = st.file_uploader(
                    "Upload system files",
                    type=['yaml', 'yml', 'md', 'txt', 'cursorrules'],
                    help="Upload config.yaml, system instructions, prompt, or rule files",
                    accept_multiple_files=True,
                    key=f"config_uploader_{len(st.session_state.loaded_rules)}"
                )
                
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if uploaded_file.name.endswith(('.yaml', '.yml')):
                            if self.load_config_file(uploaded_file):
                                st.session_state.loaded_config = uploaded_file.name
                                st.success("Configuration loaded successfully!")
                        elif uploaded_file.name not in st.session_state.loaded_rules:
                            # Store other file contents in session state
                            content = uploaded_file.getvalue().decode('utf-8')
                            st.session_state.loaded_rules[uploaded_file.name] = content
                            st.success(f"Rule file loaded: {uploaded_file.name}")
            
            # Patterns tab - contains ignore patterns
            with patterns_tab:
                st.markdown("### Ignored Patterns")
                
                # Show directories in expander
                with st.expander("Directories", expanded=False):
                    dirs = st.session_state.config.get('ignore_patterns', {}).get('directories', [])
                    dirs_text = st.text_area(
                        "Edit directories to ignore (one per line)",
                        value="\n".join(dirs) if dirs else "",
                        height=200,
                        label_visibility="collapsed",
                        key="ignore_dirs"
                    )
                    if dirs_text != "\n".join(dirs):
                        new_dirs = [d.strip() for d in dirs_text.split("\n") if d.strip()]
                        st.session_state.config['ignore_patterns']['directories'] = new_dirs
                        # Preserve loaded config state
                        current_config = st.session_state.config.copy()
                        self.save_config(current_config)
                        # Force crawler refresh
                        if 'current_tree' in st.session_state:
                            del st.session_state.current_tree
                        st.rerun()
                
                # Show files in expander
                with st.expander("Files", expanded=False):
                    files = st.session_state.config.get('ignore_patterns', {}).get('files', [])
                    files_text = st.text_area(
                        "Edit files to ignore (one per line)",
                        value="\n".join(files) if files else "",
                        height=200,
                        label_visibility="collapsed",
                        key="ignore_files"
                    )
                    if files_text != "\n".join(files):
                        new_files = [f.strip() for f in files_text.split("\n") if f.strip()]
                        st.session_state.config['ignore_patterns']['files'] = new_files
                        # Preserve loaded config state
                        current_config = st.session_state.config.copy()
                        self.save_config(current_config)
                        # Force crawler refresh
                        if 'current_tree' in st.session_state:
                            del st.session_state.current_tree
                        st.rerun()
                
                # Add direct download button for config
                config_str = yaml.dump(st.session_state.config, default_flow_style=False)
                st.download_button(
                    "💾 Save Configs",
                    config_str,
                    file_name="config.yaml",
                    mime="application/x-yaml",
                    help="Download current configuration as config.yaml"
                )
                
                return repo_path 