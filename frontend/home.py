import streamlit as st
from backend.core.crawler import RepositoryCrawler
from backend.core.file_handler import FileHandler
from frontend.components.file_tree import render_file_tree
from frontend.components.file_viewer import render_file_viewer
from backend.core.tokenizer import TokenCalculator, get_available_models

def render():
    """Render the home page."""
    st.sidebar.title("Repository Crawler 🔍")
    
    # Repository path input in sidebar
    repo_path = st.sidebar.text_input(
        "Repository Path",
        placeholder="Enter the path to your repository"
    )
    
    # Model selection in sidebar
    model = st.sidebar.selectbox(
        "Select Model for Token Analysis",
        options=get_available_models(),
        index=2  # Default to gpt-4
    )

    # Create main tabs at the top
    overview_tab, explorer_tab, chat_tab = st.tabs([
        "Codebase Overview",
        "File Explorer",
        "LLM Chat 💬"
    ])
    
    with overview_tab:
        if repo_path and st.sidebar.button("Analyze Repository"):
            with st.spinner("Analyzing repository..."):
                try:
                    # Initialize components
                    crawler = RepositoryCrawler()
                    file_handler = FileHandler()
                    token_calculator = TokenCalculator()
                    
                    # Crawl repository
                    tree_str, file_paths = crawler.crawl(repo_path)
                    
                    st.title("Codebase Parser 📊")
                    
                    # Generate Prompt button
                    st.button("Generate Prompt", key="generate_prompt")
                    
                    st.subheader("Token Analysis")
                    # Token analysis metrics in a row
                    col1, col2, col3, col4 = st.columns(4)
                    analysis = token_calculator.analyze_text(tree_str, model)
                    
                    with col1:
                        st.metric("Total Tokens", f"{analysis['token_count']:,}")
                    with col2:
                        st.metric("Input Cost", f"${analysis['input_cost']:.2f}")
                    with col3:
                        st.metric("Output Cost", f"${analysis['output_cost']:.2f}")
                    with col4:
                        st.metric("Total Size", f"{analysis['size_kb']:.1f} KB")
                    
                    st.subheader("Codebase Prompt")
                    st.markdown("Use this prompt to provide codebase context to AI")
                    
                    # Repository structure
                    st.code(tree_str, language="text")
                        
                except Exception as e:
                    st.error(f"Error analyzing repository: {str(e)}")
        else:
            st.warning("Please set a repository path in the sidebar first.")
            
    with explorer_tab:
        if repo_path and 'tree_str' in locals():
            # Split into columns for tree and viewer
            col1, col2 = st.columns([1, 2])
            with col1:
                render_file_tree(tree_str)
            with col2:
                if selected_file := render_file_viewer(file_paths, file_handler):
                    st.download_button(
                        "Download Analysis",
                        selected_file,
                        file_name="repository_analysis.txt"
                    )
        else:
            st.warning("Please analyze a repository first.")
            
    with chat_tab:
        render_chat()

def render_chat():
    """Render the chat interface."""
    st.title("Codebase Chat Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask anything about the repository..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                # Here you would normally call your LLM API
                response = f"I understand you're asking about: {prompt}"
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}") 