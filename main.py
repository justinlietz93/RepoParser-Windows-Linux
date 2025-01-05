import logging
from pathlib import Path
from datetime import datetime
import streamlit as st
import yaml

# Create logs directory
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging
log_file = logs_dir / f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting application, logging to {log_file}")

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
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error("Failed to load configuration file")
            # Create default config if file doesn't exist
            st.session_state.config = {
                'ignore_patterns': {'directories': [], 'files': []},
                'model': 'gpt-3.5-turbo'
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
