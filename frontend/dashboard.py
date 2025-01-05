import streamlit as st
import logging
from pathlib import Path
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenAnalyzer
from frontend.components.file_tree import FileTreeComponent
from frontend.components.file_viewer import FileViewer
from frontend.components.sidebar import SidebarComponent
from frontend.codebase_view import render_codebase_view

logger = logging.getLogger(__name__)

def render_file_explorer(repo_path):
    """Render the file explorer tab."""
    if repo_path and Path(repo_path).exists():
        try:
            logger.info(f"Analyzing repository: {repo_path}")
            
            # Store crawler in session state to detect config changes
            config_hash = str(hash(str(st.session_state.config)))
            if 'crawler' not in st.session_state or 'config_hash' not in st.session_state or st.session_state.config_hash != config_hash:
                # Initialize crawler with root path and config
                st.session_state.crawler = RepositoryCrawler(repo_path, st.session_state.config)
                st.session_state.config_hash = config_hash
                # Clear file tree cache to force refresh
                if 'current_tree' in st.session_state:
                    del st.session_state.current_tree
            
            # Initialize analyzer
            analyzer = TokenAnalyzer()
            
            # Create columns for tree and content
            tree_col, content_col = st.columns([1, 2])
            
            with tree_col:
                # Force file tree refresh when config changes
                file_tree = FileTreeComponent(st.session_state.crawler.get_file_tree())
                selected_file = file_tree.render()
                
                if selected_file:
                    logger.debug(f"File selected: {selected_file}")
                    st.session_state.selected_file = selected_file
            
            with content_col:
                if hasattr(st.session_state, 'selected_file') and st.session_state.selected_file:
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
    # Initialize persistent state
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["Codebase Overview", "File Explorer"])
    
    # Render sidebar and get repo path
    sidebar = SidebarComponent()
    repo_path = sidebar.render()
    
    # Render main content based on selected tab
    with tab1:
        render_codebase_view()
    
    with tab2:
        if repo_path:
            with st.spinner("Analyzing repository..."):
                render_file_explorer(repo_path)
        else:
            st.info("Please enter a valid repository path in the sidebar to begin analysis.")
    
    # Update active tab based on user selection
    for i, tab in enumerate([tab1, tab2]):
        if tab.selected:
            st.session_state.active_tab = i 