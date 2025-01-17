import streamlit as st
import logging
from pathlib import Path
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenAnalyzer
from frontend.components.file_tree import FileTreeComponent
from frontend.components.file_viewer import FileViewer
from frontend.components.sidebar import SidebarComponent
from frontend.codebase_view import render_codebase_view as render_parser_view
import time
import json

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

def render_chat():
    """Render the chat interface."""
    st.markdown("### LLM Chat Interface")
    
    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add system instructions as first message
        system_instructions = """You are an expert AI code assistant analyzing a repository. Your goal is to help users understand and work with the codebase that has been shared with you.

Key Information:
- You will receive the codebase information in multiple chunks due to size limitations
- Each chunk will be marked with its position (e.g., "Chunk 1/3")
- DO NOT respond to any questions until you have received all chunks
- While receiving chunks, focus on:
  * Building a mental model of the codebase structure
  * Understanding file relationships and dependencies
  * Noting key architectural patterns and design decisions
  * Identifying important implementation details
- After receiving all chunks, you can begin answering questions
- If you need to review specific files or sections, ask the user to regenerate the codebase context

Your capabilities:
1. Explain code structure and functionality
2. Answer questions about the implementation
3. Suggest improvements and best practices
4. Help with debugging and issue resolution
5. Provide guidance on adding new features
6. Explain architectural decisions

Remember: Do not provide any analysis or answers until you have received all chunks. Simply acknowledge each chunk with "Analyzing chunk X/Y..." and wait for the complete context."""

        st.session_state.messages.append({"role": "system", "content": system_instructions})

    # Add navigation buttons at the top
    col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
    with col1:
        if st.button("⬇️ Jump to Next Reply", use_container_width=True, key="next_reply"):
            st.components.v1.html("""
                <script>
                    setTimeout(function() {
                        const replies = document.querySelectorAll('[data-testid="stChatMessage"][data-testid*="assistant"]');
                        if (replies.length > 0) {
                            const scrollPos = window.scrollY;
                            for (const reply of replies) {
                                const replyPos = reply.getBoundingClientRect().top + window.scrollY;
                                if (replyPos > scrollPos + 10) {
                                    reply.scrollIntoView({ behavior: 'smooth' });
                                    break;
                                }
                            }
                        }
                    }, 100);
                </script>
            """, height=0)
    with col2:
        if st.button("⏬ Jump to Bottom", use_container_width=True, key="bottom"):
            st.components.v1.html("""
                <script>
                    setTimeout(function() {
                        const messages = document.querySelector('[data-testid="stChatMessageContainer"]');
                        if (messages) {
                            window.scrollTo({
                                top: document.body.scrollHeight,
                                behavior: 'smooth'
                            });
                        }
                    }, 100);
                </script>
            """, height=0)
    with col3:
        if st.button("🔄 Clear Chat", use_container_width=True, key="clear"):
            # Keep system message but clear the rest
            system_msg = st.session_state.messages[0]
            st.session_state.messages = [system_msg]
            st.rerun()

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        # Skip the first (system) message when displaying
        for message in st.session_state.messages[1:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # If there's a pending prompt chunks, show them in an editable text area first
    if "pending_prompt_chunks" in st.session_state:
        chunks = st.session_state.pending_prompt_chunks
        st.info(f"Codebase context will be sent in {len(chunks)} chunks")
        
        # Display cost estimation
        provider = st.session_state.config.get('llm_provider')
        model = st.session_state.config.get('model')
        cost_estimate = estimate_token_cost(chunks, provider, model)
        
        st.warning(
            f"Estimated Processing Cost:\n"
            f"- Total Tokens: {cost_estimate['total_tokens']:,}\n"
            f"- Input Tokens: {cost_estimate['input_tokens']:,}\n"
            f"- Output Tokens: {cost_estimate['output_tokens']:,}\n"
            f"- Estimated Cost: ${cost_estimate['estimated_cost']:.3f}"
        )
        
        # Show first chunk preview
        edited_chunk = st.text_area(
            "Edit first chunk before sending:",
            value=f"[Chunk 1/{len(chunks)}]\n{chunks[0]}",
            height=300
        )
        
        col1, col2 = st.columns([0.85, 0.15])
        with col2:
            if st.button("Send All", use_container_width=True):
                with st.spinner(f"Sending {len(chunks)} chunks..."):
                    # Send each chunk as a separate message
                    for i, chunk in enumerate(chunks, 1):
                        chunk_content = f"[Chunk {i}/{len(chunks)}]\n{chunk}"
                        if i == 1:
                            # Use edited version of first chunk
                            process_chat_message(edited_chunk, show_message=True, is_chunk=True)
                        else:
                            process_chat_message(chunk_content, show_message=True, is_chunk=True)
                        # Add a small delay between chunks
                        time.sleep(0.5)
                    
                    # After all chunks are sent, ask AI to begin analysis
                    process_chat_message("All chunks have been sent. You may now begin answering questions about the codebase.", show_message=False)
                    del st.session_state.pending_prompt_chunks
                    st.rerun()
        with col1:
            if st.button("Clear", use_container_width=True):
                del st.session_state.pending_prompt_chunks
                st.rerun()
    # Regular chat input if no pending prompt
    else:
        if prompt := st.chat_input("Ask anything about the repository..."):
            process_chat_message(prompt, show_message=True)

def condense_qa_history(messages, start_idx):
    """Create condensed Q&A history from messages starting at start_idx."""
    qa_history = []
    for i in range(start_idx, len(messages), 2):
        if i + 1 < len(messages):
            # Get Q&A pair
            question = messages[i]
            answer = messages[i + 1]
            
            # Create condensed summary
            if len(question["content"]) > 100:
                # If question is long, just take first sentence or first 100 chars
                q_summary = question["content"].split('.')[0][:100] + "..."
            else:
                q_summary = question["content"]
                
            if len(answer["content"]) > 200:
                # For answers, take first and last paragraph to capture conclusion
                paragraphs = answer["content"].split('\n\n')
                if len(paragraphs) > 1:
                    a_summary = paragraphs[0] + "\n...\n" + paragraphs[-1]
                else:
                    a_summary = answer["content"][:200] + "..."
            else:
                a_summary = answer["content"]
            
            qa_history.extend([
                {"role": "user", "content": q_summary},
                {"role": "assistant", "content": a_summary}
            ])
    
    return qa_history[-4:]  # Keep last 2 Q&A pairs

def process_chunk_with_agent(chunk: str, chunk_num: int, total_chunks: int, model: str, api_key: str, provider: str) -> dict:
    """Process a single chunk with a summarizer agent."""
    system_prompt = """You are a code analysis agent responsible for summarizing a chunk of code. Your task is to:
1. Analyze the provided chunk thoroughly
2. Create a concise summary focusing on:
   - Key functionality and components
   - Important function signatures
   - Dependencies and references to other parts of the codebase
   - Architectural patterns or design decisions
3. Extract and note any crucial details that should not be lost
4. Format your response as a structured JSON with the following fields:
   - summary: A concise overview of the chunk
   - key_components: List of important functions, classes, or modules
   - dependencies: Any references to other parts of the codebase
   - crucial_details: Specific details that must be preserved
   - cross_references: References to elements that might appear in other chunks"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"[Analyzing Chunk {chunk_num}/{total_chunks}]\n{chunk}"}
    ]

    try:
        if provider == "OpenAI":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        elif provider == "Anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            return json.loads(response.content[0].text)
    except Exception as e:
        logger.error(f"Error in summarizer agent: {str(e)}")
        return {
            "summary": f"Error processing chunk {chunk_num}: {str(e)}",
            "key_components": [],
            "dependencies": [],
            "crucial_details": [],
            "cross_references": []
        }

def merge_summaries_with_coordinator(summaries: list, model: str, api_key: str, provider: str) -> str:
    """Merge chunk summaries using a coordinator agent."""
    system_prompt = """You are a coordination agent responsible for synthesizing multiple code chunk summaries into a coherent final analysis. Your task is to:
1. Review all chunk summaries
2. Identify and connect related components across chunks
3. Resolve any conflicts or inconsistencies
4. Create a comprehensive but concise final analysis that:
   - Maintains crucial technical details
   - Explains the overall architecture
   - Highlights important relationships
   - Preserves specific implementation details
Your response should be clear, well-structured, and ready to be presented to the user."""

    # Prepare summaries for coordinator
    formatted_summaries = json.dumps(summaries, indent=2)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please synthesize these chunk summaries into a final analysis:\n{formatted_summaries}"}
    ]

    try:
        if provider == "OpenAI":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content
        elif provider == "Anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                messages=messages
            )
            return response.content[0].text
    except Exception as e:
        logger.error(f"Error in coordinator agent: {str(e)}")
        return f"Error synthesizing summaries: {str(e)}"

def process_chat_message(prompt: str, show_message: bool = True, is_chunk: bool = False):
    """Process a chat message and get LLM response."""
    # Don't process empty messages
    if not prompt.strip():
        return

    # Get API configuration
    provider = st.session_state.config.get('llm_provider')
    model = st.session_state.config.get('model')
    api_key = None
    
    if provider in SidebarComponent.LLM_PROVIDERS:
        key_name = SidebarComponent.LLM_PROVIDERS[provider]["key_name"]
        api_key = st.session_state.config.get('api_keys', {}).get(key_name)

    if not api_key:
        st.error(f"Please configure your {provider} API key in the settings first.")
        return

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    if show_message:
        with st.chat_message("user"):
            st.markdown(prompt)

    # For chunks, process with multi-agent system
    if is_chunk:
        chunk_num = int(prompt.split('[Chunk ', 1)[1].split('/', 1)[0])
        total_chunks = int(prompt.split('/', 1)[1].split(']', 1)[0])
        
        # Store chunk summary in session state
        if 'chunk_summaries' not in st.session_state:
            st.session_state.chunk_summaries = []
        
        # Process chunk with summarizer agent
        summary = process_chunk_with_agent(
            prompt.split(']', 1)[1].strip(),
            chunk_num,
            total_chunks,
            model,
            api_key,
            provider
        )
        st.session_state.chunk_summaries.append(summary)
        
        # Show processing status
        status_msg = f"Analyzing chunk {chunk_num}/{total_chunks}..."
        st.session_state.messages.append({
            "role": "assistant",
            "content": status_msg
        })
        if show_message:
            with st.chat_message("assistant"):
                st.markdown(status_msg)
        
        # If this is the last chunk, merge summaries
        if chunk_num == total_chunks:
            with st.spinner("Synthesizing final analysis..."):
                final_analysis = merge_summaries_with_coordinator(
                    st.session_state.chunk_summaries,
                    model,
                    api_key,
                    provider
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_analysis
                })
                if show_message:
                    with st.chat_message("assistant"):
                        st.markdown(final_analysis)
                # Clear chunk summaries
                st.session_state.chunk_summaries = []
        return

    # For regular messages after analysis, include the final analysis in context
    with st.chat_message("assistant"):
        try:
            messages_for_api = [
                st.session_state.messages[0],  # System message
                # Find and include the final analysis message
                next(
                    (m for m in reversed(st.session_state.messages) 
                     if m["role"] == "assistant" and not "Analyzing chunk" in m["content"]),
                    None
                ),
                # Include the current question
                {"role": "user", "content": prompt}
            ]
            messages_for_api = [m for m in messages_for_api if m is not None]

            # Get response from selected provider
            if provider == "OpenAI":
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=messages_for_api
                )
                assistant_response = response.choices[0].message.content
            elif provider == "Anthropic":
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=model,
                    messages=messages_for_api
                )
                assistant_response = response.content[0].text
            else:
                st.error(f"Provider {provider} not yet implemented")
                return

            if show_message:
                st.markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            st.error(f"Error calling {provider} API: {str(e)}")
            logger.error(f"API call error: {str(e)}", exc_info=True)

def render_codebase_view():
    """Render the codebase overview."""
    from frontend.codebase_view import render_codebase_view as render_parser_view
    render_parser_view()

def render_dashboard():
    """Render the main dashboard."""
    # Get sidebar component and render it
    sidebar = SidebarComponent()
    repo_path = sidebar.render()

    # Initialize active tab if not set
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Codebase Overview"

    # Create tabs for different views
    tab_overview, tab_explorer, tab_chat = st.tabs([
        "Codebase Overview", 
        "File Explorer",
        "LLM Chat"
    ])

    # Update active tab based on session state
    if st.session_state.active_tab == "LLM Chat":
        tab_chat.active = True
        st.session_state.active_tab = None  # Reset after switching

    with tab_overview:
        render_codebase_view()

    with tab_explorer:
        render_file_explorer(repo_path)

    with tab_chat:
        render_chat() 

def estimate_token_cost(chunks: list, provider: str, model: str) -> dict:
    """Estimate token usage and cost for processing chunks with multi-agent system."""
    # Approximate tokens per chunk (using average ratios)
    tokens_per_chunk = sum(len(chunk.split()) * 1.3 for chunk in chunks)  # 1.3 multiplier for token/word ratio
    
    # Token usage for each stage
    summarizer_tokens = {
        'input': tokens_per_chunk + 300,  # Include system prompt
        'output': 500  # Average JSON summary size
    }
    
    coordinator_tokens = {
        'input': len(chunks) * 600,  # Summaries + system prompt
        'output': 1000  # Final analysis size
    }
    
    # Total tokens for all operations
    total_tokens = {
        'input': (summarizer_tokens['input'] * len(chunks)) + coordinator_tokens['input'],
        'output': (summarizer_tokens['output'] * len(chunks)) + coordinator_tokens['output']
    }
    
    # Cost calculation (per 1K tokens)
    costs = {
        'OpenAI': {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002}
        },
        'Anthropic': {
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
        }
    }
    
    if provider in costs and model in costs[provider]:
        rate = costs[provider][model]
        estimated_cost = (
            (total_tokens['input'] / 1000) * rate['input'] +
            (total_tokens['output'] / 1000) * rate['output']
        )
    else:
        estimated_cost = 0  # Unknown model/provider combination
    
    return {
        'total_tokens': sum(total_tokens.values()),
        'input_tokens': total_tokens['input'],
        'output_tokens': total_tokens['output'],
        'estimated_cost': round(estimated_cost, 3)
    } 