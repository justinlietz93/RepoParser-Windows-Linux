# C:\Github\Repo_Crawler\main.py

import logging
from pathlib import Path
from datetime import datetime

# Create logs directory and configure logging BEFORE any other imports
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging - single file per run with reduced verbosity
log_file = logs_dir / f'repo_crawler_{datetime.now().strftime("%Y%m%d")}.log'
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    # Force all loggers to match this level
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info("Starting Repository Crawler")

import streamlit as st
import yaml

# Import our packages
from frontend.components.sidebar import SidebarComponent
from frontend.components.file_tree import FileTreeComponent
from frontend.components.file_viewer import FileViewer
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenCalculator, get_available_models

# Preserve custom user rules if set
if 'loaded_rules' not in st.session_state:
    st.session_state.loaded_rules = {}

# Also ensure 'loaded_config' is defined
if 'loaded_config' not in st.session_state:
    st.session_state.loaded_config = None

def get_default_config():
    return {
        'ignore_patterns': {
            'directories': [
                '.git','__pycache__','node_modules','venv','.venv','env','.env',
                'build','dist','.idea','.vscode','.vs','bin','obj','out','target',
                'coverage','.coverage','.pytest_cache','.mypy_cache','.tox','.eggs',
                '.sass-cache','bower_components','jspm_packages','.next','.nuxt',
                '.serverless','.terraform','vendor'
            ],
            'files': [
                '*.pyc','*.pyo','*.pyd','*.so','*.dll','*.dylib','*.egg',
                '*.egg-info','*.whl','.DS_Store','.env','*.log','*.swp','*.swo',
                '*.class','*.jar','*.war','*.nar','*.ear','*.zip','*.tar.gz',
                '*.rar','*.min.js','*.min.css','*.map','.env.local',
                '.env.development.local','.env.test.local','.env.production.local',
                '.env.*','*.sqlite','*.db','*.db-shm','*.db-wal','*.suo',
                '*.user','*.userosscache','*.sln.docstates','thumbs.db','*.cache',
                '*.bak','*.tmp','*.temp','*.pid','*.seed','*.pid.lock',
                '*.tsbuildinfo','.eslintcache','.node_repl_history','.yarn-integrity',
                '.grunt','.lock-wscript'
            ]
        },
        'local_root': '',
        'model': 'gpt-4'
    }

def reset_config():
    """
    Reset config.yaml to default, preserving 'loaded_rules'.
    Only triggers if no config is in session, to avoid repeated resets on normal reruns.
    """
    try:
        config_path = Path(__file__).parent / 'config' / 'config.yaml'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        default_config = get_default_config()

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False)

        if 'config' in st.session_state:
            st.session_state.config.update(default_config)
        else:
            st.session_state.config = default_config.copy()

        if 'loaded_config' in st.session_state:
            st.session_state.loaded_config = None
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash

        logger.info("Configuration and session state reset to default values (excluding loaded_rules)")
        return True
    except Exception as e:
        logger.error(f"Error resetting configuration: {str(e)}")
        return False

def initialize_session_state():
    """
    Run once at startup to ensure there's a config in session. 
    If missing, use reset_config(). 
    Otherwise, do nothing to preserve existing session state.
    """
    if 'config' not in st.session_state:
        if reset_config():
            try:
                config_path = Path(__file__).parent / 'config' / 'config.yaml'
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # Don't initialize API clients yet
                    if 'api_keys' in config:
                        st.session_state.config = {'api_keys': config['api_keys']}
                    else:
                        st.session_state.config = {}
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
                st.error("Failed to load configuration file")
                st.session_state.config = {}

    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

def main():
    try:
        st.set_page_config(
            page_title="Repository Crawler",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        initialize_session_state()

        from frontend.dashboard import render_dashboard
        render_dashboard()
    except Exception as e:
        logger.error("Unhandled exception in main", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
