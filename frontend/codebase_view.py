import streamlit as st
import json
from pathlib import Path
import logging
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenAnalyzer

logger = logging.getLogger(__name__)

def calculate_costs(total_tokens, model="gpt-4"):
    """Calculate estimated costs based on token count and model."""
    rates = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-3.5-turbo-16k": {"input": 0.0030, "output": 0.0040}
    }
    
    rate = rates.get(model, rates["gpt-4"])
    input_cost = (total_tokens / 1000) * rate["input"]
    output_cost = (total_tokens / 1000) * rate["output"]
    
    return input_cost, output_cost

def get_file_contents(file_path):
    """Read and return file contents safely."""
    try:
        if not Path(file_path).is_file():
            logger.warning(f"Not a file or not accessible: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"Empty file: {file_path}")
                return None
            return content
    except UnicodeDecodeError:
        logger.warning(f"Binary or non-UTF-8 file skipped: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def build_codebase_json(repo_path, config):
    """Build JSON representation of the codebase."""
    try:
        crawler = RepositoryCrawler(repo_path, config)
        analyzer = TokenAnalyzer(model=config.get('model', 'gpt-4'))
        
        # Get the file tree first
        file_tree = crawler.get_file_tree()
        if not file_tree:
            logger.warning("No files found in repository")
            return {}, 0
        
        codebase_dict = {}
        total_tokens = 0
        
        def process_tree(tree_dict, current_path=""):
            """Recursively process the file tree."""
            for name, content in tree_dict.items():
                if name.startswith('__'):  # Skip error entries
                    continue
                    
                path = Path(current_path) / name
                full_path = Path(repo_path) / path
                
                if content is None:  # It's a file
                    try:
                        if not full_path.is_file():
                            logger.warning(f"File not found or not accessible: {full_path}")
                            continue
                            
                        file_content = get_file_contents(full_path)
                        if file_content is None:
                            continue
                            
                        codebase_dict[str(path)] = {
                            "content": file_content,
                            "size": full_path.stat().st_size
                        }
                        nonlocal total_tokens
                        total_tokens += analyzer.count_tokens(file_content)
                    except Exception as e:
                        logger.error(f"Error processing {path}: {str(e)}")
                        continue
                else:  # It's a directory
                    process_tree(content, path)
        
        # Start processing from the root
        process_tree(file_tree['contents'])
        
        if not codebase_dict:
            logger.warning("No valid files processed")
            return {}, 0
            
        return codebase_dict, total_tokens
            
    except Exception as e:
        logger.error(f"Error initializing repository crawler: {str(e)}")
        raise Exception(f"Error accessing repository: {str(e)}")

def build_directory_tree(codebase_dict):
    """Build a formatted directory tree structure."""
    # Convert flat paths to tree structure
    tree = {}
    for path in codebase_dict.keys():
        parts = Path(path).parts
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = None
    
    # Format tree as string
    lines = []
    
    # Add parent directory name
    parent_dir = Path(st.session_state.config.get('local_root', '')).name
    lines.append(f"{parent_dir}/")
    
    def _format_tree(node, prefix="", is_last=True, indent=""):
        entries = sorted(node.items())
        for i, (name, subtree) in enumerate(entries):
            is_last_item = i == len(entries) - 1
            connector = "└── " if is_last_item else "├── "
            
            # Add the current item
            if subtree is None:  # File
                lines.append(f"{indent}{connector}{name}")
            else:  # Directory
                lines.append(f"{indent}{connector}{name}/")
                
                # Calculate new indent for children
                new_indent = indent + ("    " if is_last_item else "│   ")
                _format_tree(subtree, prefix + "  ", is_last_item, new_indent)
    
    # Start tree with initial indent
    _format_tree(tree, indent="    ")
    
    return lines

def build_prompt(codebase_dict):
    """Build a formatted prompt from the codebase contents."""
    prompt_parts = []
    
    # Add loaded rule files at the top
    if hasattr(st.session_state, 'loaded_rules') and st.session_state.loaded_rules:
        prompt_parts.append("# Loaded Rule Files\n")
        for filename, content in st.session_state.loaded_rules.items():
            prompt_parts.append(f"## {filename}\n")
            prompt_parts.append("```")
            prompt_parts.append(content)
            prompt_parts.append("```\n")
        prompt_parts.append("\n")
    
    # Add repository structure
    prompt_parts.append("# Repository Structure\n")
    
    # Add directory tree
    prompt_parts.append("```")
    prompt_parts.extend(build_directory_tree(codebase_dict))
    prompt_parts.append("```\n")
    
    # Add file contents in XML format
    prompt_parts.append("# Codebase XML\n")
    prompt_parts.append("```xml")
    prompt_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    
    # Get parent directory name
    parent_dir = Path(st.session_state.config.get('local_root', '')).name
    prompt_parts.append(f'<{parent_dir}>')
    
    # Build a proper directory tree structure
    dir_tree = {}
    for path, info in sorted(codebase_dict.items()):
        parts = Path(path).parts
        current = dir_tree
        for part in parts[:-1]:  # Process directories
            if part not in current:
                current[part] = {}
            current = current[part]
        # Add file to its directory
        current[parts[-1]] = info
    
    def write_directory(tree, current_path="", indent_level=1):
        """Recursively write directory structure in XML format."""
        lines = []
        indent = "  " * indent_level
        
        # Process all entries
        for name, content in sorted(tree.items()):
            full_path = f"{parent_dir}/{current_path}/{name}".replace("//", "/")
            
            # If content is a dict without 'content' key, it's a directory
            if isinstance(content, dict) and 'content' not in content:
                lines.append(f'{indent}<directory name="{name}" path="{full_path}">')
                lines.extend(write_directory(content, f"{current_path}/{name}".lstrip("/"), indent_level + 1))
                lines.append(f'{indent}</directory>')
            else:  # It's a file
                lines.append(f'{indent}<file name="{name}" path="{full_path}" size="{content.get("size", 0)}">')
                lines.append(f'{indent}  <![CDATA[')
                # Indent the content
                content_lines = content["content"].splitlines()
                if content_lines:
                    lines.extend(f'{indent}    {line}' for line in content_lines)
                else:
                    lines.append(f'{indent}    {content["content"]}')
                lines.append(f'{indent}  ]]>')
                lines.append(f'{indent}</file>')
        
        return lines
    
    # Generate XML content
    prompt_parts.extend(write_directory(dir_tree))
    prompt_parts.append(f'</{parent_dir}>')
    prompt_parts.append("```\n")
    
    return "\n".join(prompt_parts)

def get_model_token_limit(model="gpt-4"):
    """Get the token limit for a specific model."""
    limits = {
        "gpt-4": 8192,  # 8k context
        "gpt-4-32k": 32768,  # 32k context
        "gpt-3.5-turbo": 4096,  # 4k context
        "gpt-3.5-turbo-16k": 16384  # 16k context
    }
    return limits.get(model, 8192)  # Default to gpt-4 limit

def chunk_prompt(prompt: str, model="gpt-4"):
    """Split prompt into chunks that respect XML structure and token limits."""
    import re
    
    # Get model's token limit and set chunk size to 70%
    token_limit = get_model_token_limit(model)
    max_tokens = int(token_limit * 0.7)  # Use 70% of limit to leave more room for response and system message
    
    # Split into sections while preserving XML structure
    sections = re.split(r'(?=# (?:Loaded Rule Files|Repository Structure|Codebase XML)\n)', prompt)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for section in sections:
        # If section is XML content, split by file tags
        if section.startswith('# Codebase XML\n'):
            xml_parts = re.split(r'(?=\s{2}<file )|(?<=\s{2}</file>)', section)
            
            for part in xml_parts:
                # Skip empty parts
                if not part.strip():
                    continue
                    
                # Count tokens in this part
                analyzer = TokenAnalyzer()
                part_tokens = analyzer.count_tokens(part)
                
                # If adding this part would exceed limit, start new chunk
                if current_tokens + part_tokens > max_tokens and current_chunk:
                    # Ensure XML is properly closed
                    if any('<?xml' in x for x in current_chunk) and not any('</repository>' in x for x in current_chunk):
                        current_chunk.append('  </repository>\n```')
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                    
                    # If starting new chunk with XML content, add header
                    if not any('<?xml' in x for x in current_chunk):
                        current_chunk.extend([
                            '# Codebase XML (continued)\n',
                            '```xml',
                            '<?xml version="1.0" encoding="UTF-8"?>',
                            '<repository>'
                        ])
                
                current_chunk.append(part)
                current_tokens += part_tokens
        else:
            # For non-XML sections, add whole section if it fits
            analyzer = TokenAnalyzer()
            section_tokens = analyzer.count_tokens(section)
            
            if current_tokens + section_tokens > max_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(section)
            current_tokens += section_tokens
    
    # Add any remaining content
    if current_chunk:
        if any('<?xml' in x for x in current_chunk) and not any('</repository>' in x for x in current_chunk):
            current_chunk.append('  </repository>\n```')
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def render_codebase_view():
    """Render the codebase parser view."""
    st.title("Codebase Parser 📑")
    
    # Get repository path from session state
    repo_path = st.session_state.config.get('local_root', '')
    if not repo_path:
        st.warning("Please set a repository path in the sidebar first.")
        return

    # Initialize session state for storing the prompt if not exists
    if 'codebase_prompt' not in st.session_state:
        st.session_state.codebase_prompt = None
    if 'prompt_chunks' not in st.session_state:
        st.session_state.prompt_chunks = None

    # Create two columns for the buttons
    col1, col2 = st.columns([0.85, 0.15])
    
    # Generate Prompt button in the first (wider) column
    with col1:
        if st.button("Generate Prompt", use_container_width=True):
            with st.spinner("Analyzing codebase..."):
                try:
                    # Build codebase JSON
                    codebase_dict, total_tokens = build_codebase_json(
                        repo_path,
                        st.session_state.config
                    )
                    
                    # Get selected model
                    model = st.session_state.config.get('model', 'gpt-4')
                    
                    # Display token analysis
                    st.subheader("Token Analysis")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Tokens", f"{total_tokens:,}")
                    with col2:
                        input_cost, output_cost = calculate_costs(total_tokens, model)
                        st.metric("Input Cost", f"${input_cost:.2f}")
                    with col3:
                        st.metric("Output Cost", f"${output_cost:.2f}")
                    with col4:
                        total_size = sum(file_info.get('size', 0) for file_info in codebase_dict.values() if isinstance(file_info, dict))
                        st.metric("Total Size", f"{total_size / 1024:.1f} KB")
                    with col5:
                        token_limit = get_model_token_limit(model)
                        st.metric("Model Limit", f"{token_limit:,}")
                    
                    # Build and store the prompt
                    full_prompt = build_prompt(codebase_dict)
                    st.session_state.codebase_prompt = full_prompt
                    
                    # Chunk the prompt based on model
                    st.session_state.prompt_chunks = chunk_prompt(full_prompt, model)
                    
                    # Display the prompt
                    st.subheader("Codebase Prompt")
                    chunk_size = int(get_model_token_limit(model) * 0.8)
                    st.text(f"Prompt will be sent in {len(st.session_state.prompt_chunks)} chunks (max {chunk_size:,} tokens each)")
                    st.code(st.session_state.codebase_prompt, language="xml")
                    
                except Exception as e:
                    logger.error(f"Error generating codebase overview: {str(e)}")
                    st.error(f"Error generating codebase overview: {str(e)}")
    
    # Send to Chat button in the second (narrower) column
    with col2:
        if st.button("Send to Chat", use_container_width=True, disabled=not st.session_state.codebase_prompt):
            st.session_state.pending_prompt_chunks = st.session_state.prompt_chunks
            st.session_state.active_tab = "LLM Chat"
            st.rerun()

if __name__ == "__main__":
    render_codebase_view() 