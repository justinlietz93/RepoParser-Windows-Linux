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
                '.serverless','.terraform','vendor',
                # Queue directories
                'queues', '**/queues/**', '**/queue', '**/queue/**',
                '**/default/queue', '**/default/queues',
                '**/default/request_queues/**', '**/storage/request_queues/**'
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
                '.grunt','.lock-wscript',
                # Queue files
                '**/*.queue.json', '**/*.request.json', '**/*.response.json',
                '**/queues/**/*.json', '**/queue/**/*.json',
                '**/default/request_queues/**/*.json', '**/storage/request_queues/**/*.json'
            ]
        },
        'local_root': '',
        'model': 'gpt-4'
    }

def load_config():
    """Load config from disk, merging with defaults."""
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    default_config = get_default_config()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                disk_config = yaml.safe_load(f) or {}
                
            # Deep merge the configs
            merged_config = default_config.copy()
            if disk_config and isinstance(disk_config, dict):
                if 'ignore_patterns' in disk_config:
                    if 'directories' in disk_config['ignore_patterns']:
                        merged_config['ignore_patterns']['directories'].extend(
                            [d for d in disk_config['ignore_patterns']['directories'] 
                             if d not in merged_config['ignore_patterns']['directories']]
                        )
                    if 'files' in disk_config['ignore_patterns']:
                        merged_config['ignore_patterns']['files'].extend(
                            [f for f in disk_config['ignore_patterns']['files']
                             if f not in merged_config['ignore_patterns']['files']]
                        )
                
                # Merge other config keys
                for key in disk_config:
                    if key != 'ignore_patterns':
                        merged_config[key] = disk_config[key]
                        
            return merged_config
        except Exception as e:
            logger.error(f"Error loading config from disk: {str(e)}")
            return default_config
    return default_config

def save_config(config):
    """Save config to disk."""
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving config to disk: {str(e)}")
        return False

def reset_config():
    """Reset config.yaml to default, preserving custom patterns."""
    try:
        # Get current config to preserve custom patterns
        current_config = load_config() if 'config' not in st.session_state else st.session_state.config
        default_config = get_default_config()
        
        # Merge custom patterns with defaults
        if current_config and 'ignore_patterns' in current_config:
            custom_dirs = set(current_config['ignore_patterns'].get('directories', [])) - set(default_config['ignore_patterns']['directories'])
            custom_files = set(current_config['ignore_patterns'].get('files', [])) - set(default_config['ignore_patterns']['files'])
            
            if custom_dirs:
                default_config['ignore_patterns']['directories'].extend(list(custom_dirs))
            if custom_files:
                default_config['ignore_patterns']['files'].extend(list(custom_files))
        
        # Save merged config
        save_config(default_config)
        
        # Update session state
        st.session_state.config = default_config.copy()
        if 'loaded_config' in st.session_state:
            st.session_state.loaded_config = None
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
            
        logger.info("Configuration reset while preserving custom patterns")
        return True
    except Exception as e:
        logger.error(f"Error resetting configuration: {str(e)}")
        return False

def initialize_session_state():
    """Initialize session state with config from disk."""
    if 'config' not in st.session_state:
        config = load_config()
        st.session_state.config = config
        logger.info("Configuration loaded from disk")
    
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
