import streamlit as st
import json
from pathlib import Path
import logging
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenAnalyzer

logger = logging.getLogger(__name__)

def calculate_costs(total_tokens, model="gpt-3.5-turbo"):
    """Calculate estimated costs based on token count and model."""
    rates = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12}
    }
    
    rate = rates.get(model, rates["gpt-3.5-turbo"])
    input_cost = (total_tokens / 1000) * rate["input"]
    output_cost = (total_tokens / 1000) * rate["output"]
    
    return input_cost, output_cost

def get_file_contents(file_path):
    """Read and return file contents safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"

def build_codebase_json(repo_path, config):
    """Build JSON representation of the codebase."""
    crawler = RepositoryCrawler(repo_path, config)
    analyzer = TokenAnalyzer()
    codebase_dict = {}
    total_tokens = 0
    
    for root, _, files in crawler.walk():
        for file in files:
            file_path = Path(root) / file
            try:
                content = get_file_contents(file_path)
                relative_path = str(file_path.relative_to(repo_path))
                codebase_dict[relative_path] = content
                total_tokens += analyzer.count_tokens(content)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
    
    return codebase_dict, total_tokens

def render_codebase_view():
    """Render the codebase view page."""
    st.title("Codebase Overview 📚")
    
    # Get repository path from session state
    repo_path = st.session_state.config.get('local_root', '')
    if not repo_path:
        st.warning("Please set a repository path in the sidebar first.")
        return
    
    # Model selection
    model = st.selectbox(
        "Select Token Analysis Model",
        options=["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
        index=0
    )
    
    if st.button("Generate Codebase Overview"):
        with st.spinner("Analyzing codebase..."):
            try:
                # Build codebase JSON
                codebase_dict, total_tokens = build_codebase_json(
                    repo_path,
                    st.session_state.config
                )
                
                # Calculate costs
                input_cost, output_cost = calculate_costs(total_tokens, model)
                
                # Display token analysis
                st.subheader("Token Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Tokens", f"{total_tokens:,}")
                with col2:
                    st.metric("Input Cost", f"${input_cost:.2f}")
                with col3:
                    st.metric("Output Cost", f"${output_cost:.2f}")
                
                # Display codebase JSON
                st.subheader("Codebase Contents")
                st.code(
                    json.dumps(codebase_dict, indent=2),
                    language="json"
                )
                
            except Exception as e:
                logger.error(f"Error generating codebase overview: {str(e)}")
                st.error(f"Error generating codebase overview: {str(e)}")

if __name__ == "__main__":
    render_codebase_view() 