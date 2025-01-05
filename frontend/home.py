import streamlit as st
from core.crawler import RepositoryCrawler
from core.file_handler import FileHandler
from app.components.file_tree import render_file_tree
from app.components.file_viewer import render_file_viewer
from core.tokenizer import TokenCalculator, get_available_models

def render():
    """Render the home page."""
    st.title("Repository Crawler 🔍")
    
    # Repository path input
    repo_path = st.text_input(
        "Repository Path",
        placeholder="Enter the path to your repository"
    )
    
    # Add model selection for token calculation
    model = st.selectbox(
        "Select Model for Token Analysis",
        options=get_available_models(),
        index=2  # Default to gpt-4
    )
    
    if st.button("Analyze Repository") and repo_path:
        with st.spinner("Analyzing repository..."):
            try:
                # Initialize components
                crawler = RepositoryCrawler()
                file_handler = FileHandler()
                token_calculator = TokenCalculator()
                
                # Crawl repository
                tree_str, file_paths = crawler.crawl(repo_path)
                
                # Create tabs for different views
                tree_tab, content_tab, tokens_tab = st.tabs([
                    "File Tree", 
                    "File Contents",
                    "Token Analysis"
                ])
                
                with tree_tab:
                    render_file_tree(tree_str)
                
                with content_tab:
                    selected_file = render_file_viewer(file_paths, file_handler)
                    
                    if selected_file:
                        st.download_button(
                            "Download Analysis",
                            selected_file,
                            file_name="repository_analysis.txt"
                        )
                
                with tokens_tab:
                    render_token_analysis(tree_str, token_calculator, model)
                        
            except Exception as e:
                st.error(f"Error analyzing repository: {str(e)}")

def render_token_analysis(text: str, calculator: TokenCalculator, model: str):
    """Render token analysis section."""
    st.subheader("Token Analysis 🔢")
    
    analysis = calculator.analyze_text(text, model)
    
    # Display token counts and costs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Tokens",
            f"{analysis['token_count']:,}",
            help="Number of tokens in the repository analysis"
        )
    
    with col2:
        st.metric(
            "Input Cost",
            f"${analysis['input_cost']:.4f}",
            help="Estimated cost for input tokens"
        )
    
    with col3:
        st.metric(
            "Output Cost",
            f"${analysis['output_cost']:.4f}",
            help="Estimated cost for output tokens"
        )
    
    # Show sample tokens
    with st.expander("View Sample Tokens"):
        st.write("First 10 tokens in the text:")
        for token in analysis['sample_tokens']:
            st.code(f"ID: {token['id']} → {token['text']!r}") 