import logging
from pathlib import Path
from datetime import datetime

# Create logs directory and configure logging BEFORE any other imports
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging - single file per run with reduced verbosity
log_file = logs_dir / f'repo_crawler_{datetime.now().strftime("%Y%m%d")}.log'

# Only configure if logging hasn't been configured yet
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,  # Changed from DEBUG to INFO
        format='%(asctime)s [%(levelname)s] %(message)s',  # Simplified format
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Configure all loggers to use the same level
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info("Starting Repository Crawler")

# Other imports after logging is configured
import streamlit as st
import yaml

def get_default_config():
    """Return the default configuration."""
    return {
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
        'model': 'gpt-4'
    }

def reset_config():
    """Reset the config file to default values."""
    try:
        config_path = Path(__file__).parent / 'config' / 'config.yaml'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get default configuration
        default_config = get_default_config()
        
        # Write default config to file
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        # Reset all related session state
        if 'config' in st.session_state:
            st.session_state.config = default_config.copy()
        if 'loaded_config' in st.session_state:
            st.session_state.loaded_config = None
        if 'loaded_rules' in st.session_state:
            st.session_state.loaded_rules = {}
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
            
        logger.info("Configuration and session state reset to default values")
        return True
    except Exception as e:
        logger.error(f"Error resetting configuration: {str(e)}")
        return False

def initialize_session_state():
    """Initialize the session state with configuration."""
    # Reset config to default values at startup
    reset_config()
    
    if 'config' not in st.session_state:
        logger.info("Loading initial configuration")
        try:
            config_path = Path(__file__).parent / 'config' / 'config.yaml'
            with open(config_path, 'r') as f:
                st.session_state.config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error("Failed to load configuration file")
            st.session_state.config = get_default_config()

    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

# Register reset_config to run at shutdown
import atexit
atexit.register(reset_config)

def main():
    """Main application entry point."""
    try:
        # Set page config
        st.set_page_config(
            page_title="Repository Crawler",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        initialize_session_state()
        
        # Import and render dashboard
        from frontend.dashboard import render_dashboard
        render_dashboard()
        
    except Exception as e:
        logger.error("Unhandled exception in main", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
