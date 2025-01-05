import streamlit as st
import yaml
import os
from typing import Dict, Any
from pathlib import Path

def load_config() -> Dict[str, Any]:
    """Load the current configuration."""
    config_path = Path("config/config.yaml")
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return {}

def save_config(config: Dict[str, Any]) -> bool:
    """Save the configuration to file."""
    config_path = Path("config/config.yaml")
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False

def render():
    """Render the settings page."""
    st.title("Settings ⚙️")
    
    # Load current configuration
    config = load_config()
    if not config:
        st.error("Could not load configuration. Using default settings.")
        return

    # Create tabs for different settings categories
    tabs = st.tabs(["General", "Extensions", "Ignore Patterns", "Logging"])

    with tabs[0]:
        render_general_settings(config)
    
    with tabs[1]:
        render_extension_settings(config)
    
    with tabs[2]:
        render_ignore_patterns(config)
    
    with tabs[3]:
        render_logging_settings(config)

    # Save button
    if st.button("Save Settings", type="primary"):
        if save_config(config):
            st.success("Settings saved successfully!")
            st.balloons()
        else:
            st.error("Failed to save settings")

def render_general_settings(config: Dict[str, Any]):
    """Render general settings section."""
    st.header("General Settings")
    
    # Output directory settings
    config['output_directory'] = st.text_input(
        "Output Directory",
        value=config.get('output_directory', 'prompts'),
        help="Directory where analysis results will be saved"
    )
    
    # Output filename settings
    config['output_filename'] = st.text_input(
        "Output Filename",
        value=config.get('output_filename', 'repository_analysis.txt'),
        help="Default filename for analysis results"
    )

def render_extension_settings(config: Dict[str, Any]):
    """Render file extension settings section."""
    st.header("File Extensions")
    
    # Convert extensions list to multiline string for editing
    current_extensions = config.get('included_extensions', [])
    extensions_text = st.text_area(
        "Included Extensions",
        value='\n'.join(current_extensions),
        help="One extension per line (e.g., .py)",
        height=200
    )
    
    # Update config with new extensions
    config['included_extensions'] = [
        ext.strip() for ext in extensions_text.split('\n')
        if ext.strip() and ext.strip().startswith('.')
    ]

def render_ignore_patterns(config: Dict[str, Any]):
    """Render ignore patterns section."""
    st.header("Ignore Patterns")
    
    ignore_patterns = config.get('ignore_patterns', {'directories': [], 'files': []})
    
    # Directory patterns
    st.subheader("Directory Patterns")
    dir_patterns = st.text_area(
        "Ignored Directories",
        value='\n'.join(ignore_patterns.get('directories', [])),
        help="One pattern per line (e.g., node_modules)",
        height=150
    )
    ignore_patterns['directories'] = [
        pattern.strip() for pattern in dir_patterns.split('\n')
        if pattern.strip()
    ]
    
    # File patterns
    st.subheader("File Patterns")
    file_patterns = st.text_area(
        "Ignored Files",
        value='\n'.join(ignore_patterns.get('files', [])),
        help="One pattern per line (e.g., *.pyc)",
        height=150
    )
    ignore_patterns['files'] = [
        pattern.strip() for pattern in file_patterns.split('\n')
        if pattern.strip()
    ]
    
    config['ignore_patterns'] = ignore_patterns

def render_logging_settings(config: Dict[str, Any]):
    """Render logging settings section."""
    st.header("Logging Settings")
    
    logging_config = config.get('logging', {})
    
    # Log level selection
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    logging_config['level'] = st.selectbox(
        "Log Level",
        options=log_levels,
        index=log_levels.index(logging_config.get('level', 'INFO')),
        help="Set the logging level for the application"
    )
    
    # Log format
    logging_config['format'] = st.text_input(
        "Log Format",
        value=logging_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
        help="Python logging format string"
    )
    
    # Date format
    logging_config['datefmt'] = st.text_input(
        "Date Format",
        value=logging_config.get('datefmt', '%Y-%m-%d %H:%M:%S'),
        help="Python date format string for log timestamps"
    )
    
    config['logging'] = logging_config