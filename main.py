import streamlit as st
import yaml
from pathlib import Path
from core.crawler import RepositoryCrawler
from core.tokenizer import TokenAnalyzer
from app.components.file_tree import FileTreeComponent
from app.components.file_viewer import FileViewer

# Set page config
st.set_page_config(
    page_title="Repository Crawler",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'config' not in st.session_state:
    with open('config/config.yaml', 'r') as f:
        st.session_state.config = yaml.safe_load(f)

if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None

def save_config():
    """Save current configuration to config.yaml"""
    with open('config/config.yaml', 'w') as f:
        yaml.dump(st.session_state.config, f, default_flow_style=False)

def main():
    # Sidebar
    with st.sidebar:
        st.title("Repository Crawler 🔍")
        
        # Repository path input
        repo_path = st.text_input(
            "Repository Path",
            value=st.session_state.config.get('local_root', ''),
            help="Enter the full path to your local repository"
        )
        
        if repo_path:
            st.session_state.config['local_root'] = repo_path
            save_config()
        
        # File extension management
        st.subheader("File Extensions")
        extensions = st.session_state.config.get('included_extensions', [])
        new_extension = st.text_input("Add Extension", placeholder=".py")
        if new_extension and new_extension not in extensions:
            extensions.append(new_extension)
            st.session_state.config['included_extensions'] = extensions
            save_config()
        
        for ext in extensions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(ext)
            with col2:
                if st.button("❌", key=f"remove_{ext}"):
                    extensions.remove(ext)
                    st.session_state.config['included_extensions'] = extensions
                    save_config()
                    st.rerun()
        
        # Ignore patterns
        st.subheader("Ignore Patterns")
        
        # Directories to ignore
        ignore_dirs = st.session_state.config.get('ignore_patterns', {}).get('directories', [])
        new_dir = st.text_input("Add Directory to Ignore", placeholder="node_modules")
        if new_dir and new_dir not in ignore_dirs:
            ignore_dirs.append(new_dir)
            st.session_state.config['ignore_patterns']['directories'] = ignore_dirs
            save_config()
        
        for dir_name in ignore_dirs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(dir_name)
            with col2:
                if st.button("❌", key=f"remove_dir_{dir_name}"):
                    ignore_dirs.remove(dir_name)
                    st.session_state.config['ignore_patterns']['directories'] = ignore_dirs
                    save_config()
                    st.rerun()
        
        # Files to ignore
        ignore_files = st.session_state.config.get('ignore_patterns', {}).get('files', [])
        new_file = st.text_input("Add File Pattern to Ignore", placeholder="*.pyc")
        if new_file and new_file not in ignore_files:
            ignore_files.append(new_file)
            st.session_state.config['ignore_patterns']['files'] = ignore_files
            save_config()
        
        for file_pattern in ignore_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(file_pattern)
            with col2:
                if st.button("❌", key=f"remove_file_{file_pattern}"):
                    ignore_files.remove(file_pattern)
                    st.session_state.config['ignore_patterns']['files'] = ignore_files
                    save_config()
                    st.rerun()

    # Main content
    st.title("Repository Analysis")
    
    if repo_path and Path(repo_path).exists():
        try:
            # Initialize crawler and analyzer
            crawler = RepositoryCrawler(repo_path, st.session_state.config)
            analyzer = TokenAnalyzer()
            
            # Create columns for tree and content
            tree_col, content_col = st.columns([1, 2])
            
            with tree_col:
                st.subheader("File Tree")
                file_tree = FileTreeComponent(crawler.get_file_tree())
                selected_file = file_tree.render()
                
                if selected_file:
                    st.session_state.selected_file = selected_file
            
            with content_col:
                if st.session_state.selected_file:
                    st.subheader("File Content")
                    file_viewer = FileViewer(st.session_state.selected_file)
                    content = file_viewer.get_content()
                    
                    if content:
                        st.code(content, language=file_viewer.get_language())
                        
                        # Token analysis
                        tokens = analyzer.analyze_content(content)
                        st.subheader("Token Analysis")
                        st.json(tokens)
        
        except Exception as e:
            st.error(f"Error analyzing repository: {str(e)}")
    else:
        st.info("Please enter a valid repository path in the sidebar to begin analysis.")

if __name__ == "__main__":
    main()
