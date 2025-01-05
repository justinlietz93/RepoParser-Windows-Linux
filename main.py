import logging
from pathlib import Path
from datetime import datetime

# Create logs directory and configure logging BEFORE any other imports
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging - single file per run with reduced verbosity
log_file = logs_dir / f'repo_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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

def initialize_session_state():
    """Initialize the session state with configuration."""
    if 'config' not in st.session_state:
        logger.info("Loading initial configuration")
        try:
            config_path = Path(__file__).parent / 'config' / 'config.yaml'
            with open(config_path, 'r') as f:
                st.session_state.config = yaml.safe_load(f)
                # Ensure ignore_patterns exists
                if 'ignore_patterns' not in st.session_state.config:
                    st.session_state.config['ignore_patterns'] = {'directories': [], 'files': []}
                # Ensure model is set
                if 'model' not in st.session_state.config:
                    st.session_state.config['model'] = 'gpt-4'
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error("Failed to load configuration file")
            # Create default config if file doesn't exist
            st.session_state.config = {
                'ignore_patterns': {'directories': [], 'files': []},
                'model': 'gpt-4'
            }

    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

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
