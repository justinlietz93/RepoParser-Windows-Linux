# frontend/components/sidebar.py

import streamlit as st
import yaml
from pathlib import Path
import logging
from typing import Dict, Any, Optional, Callable
from threading import Lock
import subprocess
import sys
import tempfile
import os
from backend.core.crawler import RepositoryCrawler
import fnmatch
from utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

def show_file_dialog():
    """Run file dialog in a separate process to prevent freezing."""
    # Create a temporary Python script for the file dialog
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
import tkinter as tk
from tkinter import filedialog
import sys
import os

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-alpha', 0.0)  # Make window fully transparent
    root.attributes('-topmost', 1)  # Keep on top
    root.focus_force()  # Force focus
    
    try:
        # On Windows, we need to lift the window and process events
        root.lift()
        root.update()
        
        # Show the dialog
        path = filedialog.askdirectory(
            parent=root,
            title="Select Repository Directory",
            initialdir=os.path.expanduser("~")  # Start from user's home directory
        )
        
        # Print selected path if any
        if path:
            print(path)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
    finally:
        root.destroy()
''')
        temp_script = f.name

    try:
        # Run the script in a separate process
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW  # Windows-specific: prevent console window
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        elif result.stderr:
            logger.error(f"File dialog error: {result.stderr}")
            st.error(f"File dialog error: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        logger.error("File dialog timed out")
        st.error("File dialog timed out. Please try again.")
        return None
    except Exception as e:
        logger.error(f"Error in file dialog: {str(e)}")
        st.error(f"Error opening file browser: {str(e)}")
        return None
    finally:
        try:
            os.unlink(temp_script)
        except:
            pass

class SidebarComponent:
    _instance = None
    _config_lock = Lock()
    
    # Available LLM providers
    LLM_PROVIDERS = {
        "DeepSeek": {
            "key_name": "DEEPSEEK_API_KEY",
            "models": ["deepseek-chat"],
            "description": "Specialized in code analysis and generation"
        },
        "Gemini": {
            "key_name": "GEMINI_API_KEY",
            "models": ["gemini-1.5-pro-latest"],
            "description": "Strong at task coordination and synthesis",
            "is_coordinator": True
        },
        "OpenAI": {
            "key_name": "OPENAI_API_KEY",
            "models": ["gpt-4", "gpt-3.5-turbo"],
            "description": "General purpose with strong reasoning"
        },
        "Anthropic": {
            "key_name": "ANTHROPIC_API_KEY",
            "models": ["claude-3-opus", "claude-3-sonnet"],
            "description": "Excels at detailed technical analysis"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SidebarComponent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize sidebar component."""
        self.db = DatabaseManager()
        if 'config' not in st.session_state:
            st.session_state.config = {}
        
        # Load saved API keys
        saved_keys = self.db.get_api_keys()
        if saved_keys:
            st.session_state.config['api_keys'] = saved_keys
        
        # Prevent multiple initializations in the same session
        if 'sidebar_initialized' not in st.session_state:
            st.session_state.sidebar_initialized = True
            logger.info("Initializing SidebarComponent")
        
        # Define default config - this is the single source of truth
        self.default_config = {
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
            'local_root': '',
            'model': 'gpt-4',
            'llm_provider': 'OpenAI',
            'api_keys': {}  # Empty but preserved structure
        }
        self.initialize_state()
        self._initialized = True

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and repair configuration if needed."""
        # Create a new config with defaults, preserving existing API keys
        validated = self.default_config.copy()
        
        if config and isinstance(config, dict):
            # Preserve API keys if they exist
            if 'api_keys' in config and isinstance(config['api_keys'], dict):
                validated['api_keys'] = config['api_keys']
            
            # Copy other fields if they're valid
            if 'local_root' in config:
                validated['local_root'] = config['local_root']
            if 'model' in config:
                validated['model'] = config['model']
            if 'llm_provider' in config:
                validated['llm_provider'] = config['llm_provider']
            
            # Handle ignore patterns
            if 'ignore_patterns' in config and isinstance(config['ignore_patterns'], dict):
                if 'directories' in config['ignore_patterns'] and isinstance(config['ignore_patterns']['directories'], list):
                    validated['ignore_patterns']['directories'] = config['ignore_patterns']['directories']
                if 'files' in config['ignore_patterns'] and isinstance(config['ignore_patterns']['files'], list):
                    validated['ignore_patterns']['files'] = config['ignore_patterns']['files']
        
        return validated

    def initialize_state(self):
        """Initialize session state for sidebar with proper locking."""
        with self._config_lock:
            # Initialize loaded_rules if not present
            if 'loaded_rules' not in st.session_state:
                st.session_state.loaded_rules = {}

            # Ensure 'loaded_config' always exists
            if 'loaded_config' not in st.session_state:
                st.session_state.loaded_config = None

            # Also ensure 'config' exists in session state with all required fields
            if 'config' not in st.session_state:
                config_path = Path('config/config.yaml')
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            loaded_config = yaml.safe_load(f)
                            if loaded_config and isinstance(loaded_config, dict):
                                # Validate and repair config if needed
                                validated_config = self._validate_config(loaded_config)
                                st.session_state.config = validated_config
                                st.session_state.loaded_config = validated_config
                            else:
                                st.session_state.config = self._validate_config({})
                    except Exception as e:
                        logger.error(f"Error loading config: {str(e)}")
                        st.session_state.config = self._validate_config({})
                else:
                    st.session_state.config = self._validate_config({})
            else:
                # Validate existing config
                st.session_state.config = self._validate_config(st.session_state.config)

    def validate_repo_path(self, path: str) -> Optional[Path]:
        """Quick validation of repository path."""
        if not path:
            st.error("Repository path cannot be empty")
            return None
            
        try:
            # Basic path validation only
            abs_path = Path(path).absolute()
            
            # Quick security check
            path_str = str(abs_path).lower()
            if any(pattern in path_str for pattern in {'..', '~', '$', '%', '\\\\'}):
                st.error("Invalid path pattern detected")
                return None
                
            # Basic existence check
            if not abs_path.exists() or not abs_path.is_dir():
                st.error("Path must be an existing directory")
                return None
                
            return abs_path
            
        except Exception as e:
            st.error(f"Invalid repository path: {str(e)}")
            logger.error(f"Path validation error: {str(e)}", exc_info=True)
            return None

    def initialize_crawler(self, path: Path) -> Optional[RepositoryCrawler]:
        """Initialize repository crawler with size warning."""
        try:
            # Quick size check before initializing crawler
            try:
                with st.spinner("Checking repository size..."):
                    size = 0
                    file_count = 0
                    size_check_limit = 100000  # Check first 100k files
                    
                    for root, dirs, files in os.walk(path):
                        # Apply ignore patterns early
                        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in 
                            st.session_state.config.get('ignore_patterns', {}).get('directories', []))]
                        
                        for f in files:
                            if file_count > size_check_limit or size > 5_000_000_000:  # 5GB
                                warning_container = st.empty()
                                with warning_container:
                                    warning_cols = st.columns([15, 1])
                                    with warning_cols[0]:
                                        st.warning("⚠️ Large repository detected - performance optimizations enabled")
                                    with warning_cols[1]:
                                        if st.button("✕", key=f"dismiss_warning_{str(path)}", help="Dismiss warning"):
                                            warning_container.empty()
                                break
                            
                            file_path = Path(os.path.join(root, f))
                            if file_path.is_file():  # Check if it's a file before getting size
                                try:
                                    size += file_path.stat().st_size
                                    file_count += 1
                                except (OSError, IOError) as e:
                                    logger.warning(f"Could not get size of {file_path}: {e}")
                                    continue
                                    
            except Exception as e:
                logger.warning(f"Size check failed: {str(e)}")
            
            # Initialize crawler with config from session state
            crawler = RepositoryCrawler(str(path), st.session_state.config)
            st.session_state.crawler = crawler  # Use consistent cache key
            return crawler
        except Exception as e:
            logger.error(f"Failed to initialize crawler: {str(e)}")
            return None

    def safe_path_operation(self, path: Path, operation: Callable) -> Any:
        """Execute path operation with caching and chunking."""
        cache_key = f"path_op_{str(path)}_{operation.__name__}"
        
        # Return cached result if available
        if cache_key in st.session_state:
            return st.session_state[cache_key]
            
        try:
            # Execute operation with progress indicator
            with st.spinner("Loading repository structure..."):
                result = operation(path)
                st.session_state[cache_key] = result
                return result
        except Exception as e:
            logger.error(f"Path operation failed: {str(e)}")
            return None

    def validate_model_selection(self, provider: str, model: str) -> tuple[bool, str]:
        """Validate if the selected model is available for the provider."""
        if provider not in self.LLM_PROVIDERS:
            return False, f"Provider '{provider}' is not supported"
        
        available_models = self.LLM_PROVIDERS[provider]["models"]
        if model not in available_models:
            return False, f"Model '{model}' is not available for {provider}. Available models: {', '.join(available_models)}"
        
        return True, ""

    def render(self):
        """Render the sidebar component."""
        st.sidebar.title("Repository Crawler 🔍")
        
        # Create tabs for different settings
        tabs = st.sidebar.tabs(["File Settings", "LLM Settings", "File Tree"])
        
        with tabs[0]:
            self._render_file_settings()
            
        with tabs[1]:
            self._render_llm_settings()
            
        with tabs[2]:
            self._render_file_tree()

    def _render_file_settings(self):
        """Render the file settings tab."""
        st.markdown("### Repository")
        repo_path = st.text_input(
            "Path",
            value=st.session_state.config.get('local_root', ''),
            help="Enter the full path to your local repository",
            placeholder="C:/path/to/repository"
        )

        if st.button("📂 Browse for Repository", help="Browse for repository directory", use_container_width=True):
            try:
                selected_path = show_file_dialog()
                if selected_path:
                    # Validate selected path
                    validated_path = self.validate_repo_path(selected_path)
                    if validated_path:
                        repo_path = str(validated_path)
                        st.session_state.config['local_root'] = repo_path
                        
                        # Initialize crawler for browsed path
                        crawler = self.initialize_crawler(validated_path)
                        if crawler:
                            st.session_state.crawler = crawler
                            st.session_state.config_hash = str(hash(str(st.session_state.config)))
                        
                        self.save_config(st.session_state.config)
                        st.rerun()
            except Exception as e:
                st.error(f"Error opening file browser: {str(e)}")
                logger.error(f"File browser error: {str(e)}", exc_info=True)

        # Validate manually entered path
        if repo_path != st.session_state.config.get('local_root', ''):
            validated_path = self.validate_repo_path(repo_path)
            if validated_path:
                repo_path = str(validated_path)
                st.session_state.config['local_root'] = repo_path
                
                # Initialize crawler here when path changes
                if ('crawler' not in st.session_state or 
                    'config_hash' not in st.session_state or 
                    st.session_state.config_hash != str(hash(str(st.session_state.config)))):
                    
                    crawler = self.initialize_crawler(validated_path)
                    if crawler:
                        st.session_state.crawler = crawler
                        st.session_state.config_hash = str(hash(str(st.session_state.config)))
                
                self.save_config(st.session_state.config)
                st.rerun()

        # Configuration Section
        st.markdown("### Configuration")

        # Safe check for loaded_config
        if st.session_state.loaded_config:  # If not None, show success or clear button
            st.success(f"Using config: {st.session_state.loaded_config}")
            if st.button("❌ Clear All", key="clear_all_config"):
                self.clear_state()
                st.rerun()

        if st.session_state.loaded_rules:
            st.write("Loaded rules found:", list(st.session_state.loaded_rules.keys()))
            for filename in list(st.session_state.loaded_rules.keys()):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"- {filename}")
                with col2:
                    if st.button("❌", key=f"remove_rule_{filename}", help=f"Remove {filename}"):
                        del st.session_state.loaded_rules[filename]
                        st.rerun()

        uploaded_files = st.file_uploader(
            "Upload system files",
            type=['yaml', 'yml', 'md', 'txt', 'cursorrules'],
            help="Upload config.yaml, system instructions, prompt, or rule files",
            accept_multiple_files=True,
            key=f"config_uploader_{len(st.session_state.loaded_rules)}"
        )

        # Ignore Patterns Section
        st.markdown("### Ignore Patterns")

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
                st.session_state.config['ignore_patterns'] = {
                    'directories': new_dirs,
                    'files': st.session_state.config.get('ignore_patterns', {}).get('files', [])
                }
                self.save_config(st.session_state.config)
                # Clear crawler cache to force refresh
                if 'crawler' in st.session_state:
                    del st.session_state.crawler
                if 'current_tree' in st.session_state:
                    del st.session_state.current_tree
                st.rerun()

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
                st.session_state.config['ignore_patterns'] = {
                    'directories': st.session_state.config.get('ignore_patterns', {}).get('directories', []),
                    'files': new_files
                }
                self.save_config(st.session_state.config)
                # Clear crawler cache to force refresh
                if 'crawler' in st.session_state:
                    del st.session_state.crawler
                if 'current_tree' in st.session_state:
                    del st.session_state.current_tree
                st.rerun()

    def _render_llm_settings(self):
        """Render the LLM settings tab."""
        st.markdown("### LLM Settings")
        
        # Provider Selection
        current_provider = st.session_state.config.get('llm_provider', 'OpenAI')
        new_provider = st.selectbox(
            "Provider",
            options=list(self.LLM_PROVIDERS.keys()),
            index=list(self.LLM_PROVIDERS.keys()).index(current_provider) if current_provider in self.LLM_PROVIDERS else 0
        )

        # Model Selection with validation
        current_model = st.session_state.config.get('model', self.LLM_PROVIDERS[new_provider]["models"][0])
        available_models = self.LLM_PROVIDERS[new_provider]["models"]
        
        # Ensure current_model is in available_models, otherwise use first available
        if current_model not in available_models:
            current_model = available_models[0]
        
        new_model = st.selectbox(
            "Model",
            options=available_models,
            index=available_models.index(current_model)
        )

        # Update config if provider or model changed
        if new_provider != current_provider or new_model != current_model:
            is_valid, error_msg = self.validate_model_selection(new_provider, new_model)
            if is_valid:
                st.session_state.config['llm_provider'] = new_provider
                st.session_state.config['model'] = new_model
                self.save_config(st.session_state.config)
            else:
                st.error(error_msg)
                # Reset to default model for the provider
                st.session_state.config['model'] = self.LLM_PROVIDERS[new_provider]["models"][0]
                self.save_config(st.session_state.config)
                st.rerun()

        # Provider Status in Expander
        with st.expander("🔌 Provider Status", expanded=False):
            # Create columns for status display
            status_cols = st.columns(2)
            
            # Track active providers
            active_providers = []
            
            # Check each provider's status
            for i, (provider_name, provider_info) in enumerate(self.LLM_PROVIDERS.items()):
                key_name = provider_info["key_name"]
                keys = st.session_state.config.get('api_keys', {}).get(key_name, [])
                if not isinstance(keys, list):
                    keys = [keys] if keys else []
                
                # Determine status icon and color
                if keys:
                    status_icon = "🟢"
                    status_color = "green"
                    key_count = len(keys)
                    active_providers.append(provider_name)
                else:
                    status_icon = "⚪"
                    status_color = "gray"
                    key_count = 0
                
                # Display in alternating columns
                with status_cols[i % 2]:
                    st.markdown(
                        f"{status_icon} **{provider_name}**: "
                        f"<span style='color:{status_color}'>{key_count} key{'s' if key_count != 1 else ''} active</span>",
                        unsafe_allow_html=True
                    )
            
            # Show coordinator info if Gemini is configured
            if "Gemini" in active_providers:
                st.info("✨ Gemini is configured as the coordinator for multi-agent synthesis")
        
        key_name = self.LLM_PROVIDERS[new_provider]["key_name"]
        supports_multiple = self.LLM_PROVIDERS[new_provider].get("supports_multiple_keys", False)
        
        # Get existing keys for this provider
        existing_keys = st.session_state.config.get('api_keys', {}).get(key_name, [])
        if not isinstance(existing_keys, list):
            existing_keys = [existing_keys] if existing_keys else []
        
        # Show existing keys
        if existing_keys:
            st.markdown("#### Configured API Keys")
            for i, key in enumerate(existing_keys):
                masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "****"
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.text(f"Key {i+1}: {masked_key}")
                with col2:
                    if st.button("❌", key=f"remove_key_{i}", help=f"Remove key {i+1}"):
                        existing_keys.pop(i)
                        if not existing_keys:  # If last key removed
                            st.session_state.config['api_keys'][key_name] = []
                        else:
                            st.session_state.config['api_keys'][key_name] = existing_keys
                        self.save_config(st.session_state.config)
                        st.rerun()
        
        # Add new key section
        st.markdown("#### Add New API Key")
        new_api_key = st.text_input(
            f"Enter {key_name}",
            type="password",
            key=f"new_api_key_{new_provider}"
        )
        
        if new_api_key:
            try:
                # Validate API key before saving
                if new_provider == "OpenAI":
                    if not new_api_key.startswith("sk-"):
                        st.error("Invalid OpenAI API key format. Should start with 'sk-'")
                        return repo_path
                    # Test the API key
                    from openai import OpenAI
                    client = OpenAI(api_key=new_api_key)
                    try:
                        # Make a minimal API call to validate the key
                        client.models.list()
                        valid_key = True
                    except Exception as e:
                        st.error(f"Invalid OpenAI API key: {str(e)}")
                        return repo_path
                elif new_provider == "Anthropic":
                    if not new_api_key.startswith("sk-ant-"):
                        st.error("Invalid Anthropic API key format. Should start with 'sk-ant-'")
                        return repo_path
                    # Test the API key
                    try:
                        from anthropic import Anthropic
                        client = Anthropic(api_key=new_api_key)
                        # Make a minimal API call to validate the key
                        client.messages.create(
                            model="claude-3-sonnet",
                            max_tokens=1,
                            messages=[{"role": "user", "content": "Hi"}]
                        )
                        valid_key = True
                    except Exception as e:
                        st.error(f"Invalid Anthropic API key: {str(e)}")
                        return repo_path
                elif new_provider == "DeepSeek":
                    # Test the DeepSeek API key
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=new_api_key, base_url="https://api.deepseek.com/v1")
                        # Make a minimal API call to validate the key
                        response = client.models.list()
                        valid_key = True
                    except Exception as e:
                        st.error(f"Invalid DeepSeek API key: {str(e)}")
                        return repo_path
                elif new_provider == "Gemini":
                    # Validate Gemini API key by testing it
                    try:
                        import google.generativeai as genai
                        # Ensure we're passing a string, not a list
                        if isinstance(new_api_key, list):
                            new_api_key = new_api_key[0] if new_api_key else None
                        if not new_api_key:
                            st.error("Invalid Gemini API key")
                            return repo_path
                        genai.configure(api_key=new_api_key)
                        # Just get the models list instead of generating content
                        models = genai.list_models()
                        valid_key = True
                    except Exception as e:
                        st.error(f"Invalid Gemini API key: {str(e)}")
                        return repo_path
                
                # Only save if validation passed
                if 'api_keys' not in st.session_state.config:
                    st.session_state.config['api_keys'] = {}
                
                # Initialize as list if not already
                if key_name not in st.session_state.config['api_keys']:
                    st.session_state.config['api_keys'][key_name] = []
                elif not isinstance(st.session_state.config['api_keys'][key_name], list):
                    # Convert single key to list
                    old_key = st.session_state.config['api_keys'][key_name]
                    st.session_state.config['api_keys'][key_name] = [old_key] if old_key else []
                
                # Add new key if not already present
                if new_api_key not in st.session_state.config['api_keys'][key_name]:
                    st.session_state.config['api_keys'][key_name].append(new_api_key)
                    st.session_state.config['llm_provider'] = new_provider
                    st.session_state.config['model'] = new_model
                    self.save_config(st.session_state.config)
                    st.success(f"{new_provider} API key added successfully!")
                    st.rerun()
                else:
                    st.warning("This API key is already configured.")
                    
            except Exception as e:
                st.error(f"Error saving API key: {str(e)}")
                logger.error(f"API key save error: {str(e)}", exc_info=True)
                return repo_path

    def _render_file_tree(self):
        """Render the file tree tab."""
        repo_path = st.session_state.config.get('local_root', '')
        if not repo_path:
            st.info("Please enter a repository path in the File Settings tab.")
            return repo_path
            
        # Quick path validation
        validated_path = self.validate_repo_path(repo_path)
        if not validated_path:
            return repo_path
            
        try:
            # Use existing crawler from session state
            crawler = st.session_state.get('crawler')
            if not crawler:
                st.error("Repository crawler not initialized. Please check the repository path.")
                return repo_path
            
            # Get file tree
            file_tree = crawler.get_file_tree()
            if not file_tree:
                st.error("Failed to get file tree")
                return repo_path
            
            # Use the VS Code-style tree view
            from frontend.components.tree_view import TreeView
            tree_view = TreeView()
            
            # Add message handler for tree view toggle events
            def handle_tree_toggle():
                """Handle tree view checkbox toggle events."""
                import streamlit.components.v1 as components
                
                # Create a container for the message handler
                components.html(
                    """
                    <script>
                        window.addEventListener('message', function(event) {
                            if (event.data.type === 'tree_toggle') {
                                const data = event.data.data;
                                window.parent.Streamlit.setComponentValue({
                                    path: data.path,
                                    type: data.type,
                                    checked: data.checked
                                });
                            }
                        });
                    </script>
                    """,
                    height=0
                )
                
                # Get the toggle event data
                toggle_data = st.session_state.get('_last_tree_toggle')
                if toggle_data:
                    path = toggle_data.get('path')
                    item_type = toggle_data.get('type')
                    checked = toggle_data.get('checked')
                    
                    if path and item_type:
                        # Update ignore patterns based on toggle
                        if item_type == 'dir':
                            dirs = set(st.session_state.config.get('ignore_patterns', {}).get('directories', []))
                            if checked:
                                dirs.discard(path)
                            else:
                                dirs.add(path)
                            st.session_state.config['ignore_patterns']['directories'] = sorted(list(dirs))
                        else:  # file
                            files = set(st.session_state.config.get('ignore_patterns', {}).get('files', []))
                            if checked:
                                files.discard(path)
                            else:
                                files.add(path)
                            st.session_state.config['ignore_patterns']['files'] = sorted(list(files))
                        
                        # Save updated config
                        self.save_config(st.session_state.config)
                        st.rerun()
            
            # Add the message handler
            handle_tree_toggle()
            
            # Render the tree view
            tree_view.render(
                file_tree['contents'],
                ignored_dirs=set(st.session_state.config.get('ignore_patterns', {}).get('directories', [])),
                ignored_files=set(st.session_state.config.get('ignore_patterns', {}).get('files', []))
            )
            
        except Exception as e:
            st.error(f"Error loading file tree: {str(e)}")
            logger.error(f"File tree error: {str(e)}", exc_info=True)
            return repo_path

    def save_config(self, config_data: Dict[str, Any]):
        """Save configuration to config.yaml with proper locking."""
        try:
            with self._config_lock:
                logger.info("Saving config")
                config_path = Path('config/config.yaml')
                config_path.parent.mkdir(parents=True, exist_ok=True)

                # Validate the config first
                validated_config = self._validate_config(config_data)
                
                # Create a copy for file saving (without API keys)
                save_data = validated_config.copy()
                save_data['api_keys'] = {}  # Clear API keys only for file storage
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(save_data, f, default_flow_style=False, sort_keys=False)

                # Keep the full validated config (with API keys) in session state
                st.session_state.config = validated_config
                return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            st.error(f"Failed to save configuration: {str(e)}")
            return False

    def clear_state(self):
        """Clear all sidebar-related state."""
        # Create a fresh default config without any API keys
        fresh_config = self.default_config.copy()
        fresh_config['api_keys'] = {}
        
        st.session_state.config = fresh_config
        st.session_state.loaded_config = None
        st.session_state.loaded_rules = {}
        
        # Clear crawler and related caches
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
            
        # Save the cleared config to file
        self.save_config(fresh_config)

    def load_config_file(self, uploaded_file) -> bool:
        """Load configuration from uploaded file."""
        try:
            content = uploaded_file.getvalue().decode()
            config_data = yaml.safe_load(content)
            required_keys = {'local_root', 'ignore_patterns', 'model'}
            if not all(k in config_data for k in required_keys):
                st.error("Invalid configuration file format")
                return False
            return self.save_config(config_data)
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error(f"Error loading configuration: {str(e)}")
            return False
