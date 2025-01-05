import streamlit as st
from core.crawler import RepositoryCrawler
from core.file_handler import FileHandler
from app.components.file_tree import render_file_tree
from app.components.file_viewer import render_file_viewer

def render():
    """Render the home page."""
    st.title("Repository Crawler 🔍")
    
    # Repository path input
    repo_path = st.text_input(
        "Repository Path",
        placeholder="Enter the path to your repository"
    )
    
    if st.button("Analyze Repository") and repo_path:
        with st.spinner("Analyzing repository..."):
            try:
                # Initialize core components
                crawler = RepositoryCrawler()
                file_handler = FileHandler()
                
                # Crawl repository
                tree_str, file_paths = crawler.crawl(repo_path)
                
                # Display results in two columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("File Tree")
                    render_file_tree(tree_str)
                
                with col2:
                    st.subheader("File Contents")
                    selected_file = render_file_viewer(file_paths, file_handler)
                    
                    if selected_file:
                        st.download_button(
                            "Download Analysis",
                            selected_file,
                            file_name="repository_analysis.txt"
                        )
                        
            except Exception as e:
                st.error(f"Error analyzing repository: {str(e)}") 