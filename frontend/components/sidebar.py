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
    
    def render(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("Repository Crawler 🔍")
            
            # Config file upload
            st.markdown("### Configuration")
            uploaded_file = st.file_uploader(
                "Upload a custom config.yaml file",
                type=['yaml', 'yml'],
                help="Upload a configuration file to load settings",
                key="config_uploader"
            )
            
            if uploaded_file:
                if self.load_config_file(uploaded_file):
                    st.success("Configuration loaded successfully!")
                    # Clear the file uploader state
                    st.session_state.config_uploader = None
                    st.rerun()
            
            # Repository path
            st.markdown("### Repository")
            repo_path = st.text_input(
                "Path",
                value=st.session_state.config.get('local_root', ''),
                help="Enter the full path to your local repository",
                placeholder="C:/path/to/repository"
            )
            
            if repo_path != st.session_state.config.get('local_root', ''):
                st.session_state.config['local_root'] = repo_path
                self.save_config({'local_root': repo_path})
            
            # Show ignore patterns
            with st.expander("Ignore Patterns", expanded=False):
                st.markdown("#### Currently Ignored")
                
                # Show directories
                st.markdown("**Directories:**")
                dirs = st.session_state.config.get('ignore_patterns', {}).get('directories', [])
                if dirs:
                    st.code("\n".join(dirs))
                
                # Show files
                st.markdown("**Files:**")
                files = st.session_state.config.get('ignore_patterns', {}).get('files', [])
                if files:
                    st.code("\n".join(files))
                
                st.markdown("*Edit config.yaml to modify ignore patterns*")
            
            return repo_path 