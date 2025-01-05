import streamlit as st
import yaml
from pathlib import Path
import logging
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenAnalyzer
from frontend.components.file_tree import FileTreeComponent
from frontend.components.file_viewer import FileViewer
from frontend.codebase_view import render_codebase_view

logger = logging.getLogger(__name__)

def save_config():
    """Save current configuration to config.yaml"""
    logger.info("Saving configuration")
    try:
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(st.session_state.config, f, default_flow_style=False)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        st.error("Failed to save configuration")

def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.title("Repository Crawler 🔍")
        
        # Repository path input
        repo_path = st.text_input(
            "Repository Path",
            value=st.session_state.config.get('local_root', ''),
            help="Enter the full path to your local repository"
        )
        
        if repo_path:
            logger.debug(f"Repository path updated: {repo_path}")
            st.session_state.config['local_root'] = repo_path
            save_config()
        
        with st.expander("About File Scanning", expanded=True):
            st.markdown("""
            By default, all files in the repository will be scanned unless explicitly ignored.
            Use the ignore patterns below to exclude specific files or directories.
            """)
        
        # Ignore patterns section
        with st.expander("Ignore Patterns", expanded=True):
            # Directories to ignore
            st.subheader("Directories")
            ignore_dirs = st.session_state.config.get('ignore_patterns', {}).get('directories', [])
            new_dir = st.text_input(
                "Add Directory to Ignore", 
                placeholder="node_modules",
                help="Enter directory names or patterns to ignore (e.g., node_modules, .git, __pycache__)"
            )
            if new_dir and new_dir not in ignore_dirs:
                logger.info(f"Adding directory to ignore: {new_dir}")
                ignore_dirs.append(new_dir)
                st.session_state.config['ignore_patterns']['directories'] = ignore_dirs
                save_config()
            
            if ignore_dirs:
                st.markdown("##### Current Ignored Directories")
                for dir_name in ignore_dirs:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(dir_name)
                    with col2:
                        if st.button("❌", key=f"remove_dir_{dir_name}"):
                            logger.info(f"Removing ignored directory: {dir_name}")
                            ignore_dirs.remove(dir_name)
                            st.session_state.config['ignore_patterns']['directories'] = ignore_dirs
                            save_config()
                            st.rerun()
            
            # Files to ignore
            st.markdown("---")
            st.subheader("Files")
            ignore_files = st.session_state.config.get('ignore_patterns', {}).get('files', [])
            new_file = st.text_input(
                "Add File Pattern to Ignore", 
                placeholder="*.pyc",
                help="Enter file patterns to ignore (e.g., *.pyc, *.log, .DS_Store)"
            )
            if new_file and new_file not in ignore_files:
                logger.info(f"Adding file pattern to ignore: {new_file}")
                ignore_files.append(new_file)
                st.session_state.config['ignore_patterns']['files'] = ignore_files
                save_config()
            
            if ignore_files:
                st.markdown("##### Current Ignored Files")
                for file_pattern in ignore_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(file_pattern)
                    with col2:
                        if st.button("❌", key=f"remove_file_{file_pattern}"):
                            logger.info(f"Removing ignored file pattern: {file_pattern}")
                            ignore_files.remove(file_pattern)
                            st.session_state.config['ignore_patterns']['files'] = ignore_files
                            save_config()
                            st.rerun()
        
        # Add settings section
        with st.expander("Settings", expanded=False):
            st.markdown("##### Token Analysis Model")
            model = st.selectbox(
                "Select Model",
                options=["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
                index=0,
                help="Select the model to use for token analysis"
            )
            if model != st.session_state.config.get('model', 'gpt-3.5-turbo'):
                logger.info(f"Changing token analysis model to: {model}")
                st.session_state.config['model'] = model
                save_config()
    
    return repo_path

def render_file_explorer(repo_path):
    """Render the file explorer tab."""
    st.title("Repository Analysis")
    
    if repo_path and Path(repo_path).exists():
        try:
            logger.info(f"Analyzing repository: {repo_path}")
            # Initialize crawler with root path and config
            crawler = RepositoryCrawler(repo_path, st.session_state.config)
            analyzer = TokenAnalyzer()
            
            # Create columns for tree and content
            tree_col, content_col = st.columns([1, 2])
            
            with tree_col:
                st.subheader("File Tree")
                file_tree = FileTreeComponent(crawler.get_file_tree())
                selected_file = file_tree.render()
                
                if selected_file:
                    logger.debug(f"File selected: {selected_file}")
                    st.session_state.selected_file = selected_file
            
            with content_col:
                if st.session_state.selected_file:
                    st.subheader("File Content")
                    file_viewer = FileViewer(
                        st.session_state.selected_file,
                        repo_root=repo_path
                    )
                    content = file_viewer.get_content()
                    
                    if content:
                        st.code(content, language=file_viewer.get_language())
                        
                        # Token analysis
                        logger.debug("Performing token analysis")
                        tokens = analyzer.analyze_content(content)
                        st.subheader("Token Analysis")
                        st.json(tokens)
        
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}", exc_info=True)
            st.error(f"Error analyzing repository: {str(e)}")
    else:
        logger.info("Waiting for valid repository path")
        st.info("Please enter a valid repository path in the sidebar to begin analysis.")

def render_dashboard():
    """Main dashboard rendering function."""
    # Navigation tabs
    tab1, tab2 = st.tabs(["Codebase Overview", "File Explorer"])
    
    # Render sidebar and get repo path
    repo_path = render_sidebar()
    
    # Render main content
    with tab1:
        render_codebase_view()
    
    with tab2:
        render_file_explorer(repo_path) 