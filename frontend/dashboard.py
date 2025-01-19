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
from time import sleep
import json
import asyncio
import aiohttp
from chromadb import Client, Settings
import numpy as np
from openai import OpenAI, AsyncOpenAI
from anthropic import Anthropic, AsyncAnthropic
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

def render_file_explorer(repo_path):
    """Render the file explorer tab."""
    if not repo_path:
        st.info("Please enter a repository path in the sidebar to begin analysis.")
        return
        
    if not Path(repo_path).exists():
        st.error("The specified repository path does not exist.")
        return
        
    # Initialize crawler only when explicitly requested
    if st.button("Analyze Files", key="analyze_files"):
        try:
            # Only initialize crawler if needed
            config_hash = str(hash(str(st.session_state.config)))
            if ('crawler' not in st.session_state or 
                'config_hash' not in st.session_state or 
                st.session_state.config_hash != config_hash):
                
                logger.info(f"Initializing crawler for: {repo_path}")
                st.session_state.crawler = RepositoryCrawler(repo_path, st.session_state.config)
                st.session_state.config_hash = config_hash
                if 'current_tree' in st.session_state:
                    del st.session_state.current_tree
            
            # Initialize analyzer
            analyzer = TokenAnalyzer()
            
            # Create columns for tree and content
            tree_col, content_col = st.columns([1, 2])
            
            with tree_col:
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
        st.info("Click 'Analyze Files' to view the repository structure.")

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
            f"- Estimated Cost: ${cost_estimate['estimated_cost']:.4f}"
        )
        
        # For single chunk, allow configuring multiple agents
        if len(chunks) == 1:
            st.info("Single chunk detected - you can use multiple agents for analysis")
            num_agents = st.slider(
                "Number of Analysis Agents",
                min_value=1,
                max_value=25,
                value=3,
                help="How many agents should independently analyze the code before reaching consensus"
            )
            
            # Store agent count in session state
            st.session_state.num_analysis_agents = num_agents
            
            # Show estimated cost with multiple agents
            multi_agent_cost = estimate_token_cost(chunks * num_agents, provider, model)
            st.warning(
                f"Multi-Agent Cost Estimate:\n"
                f"- Total Tokens: {multi_agent_cost['total_tokens']:,}\n"
                f"- Estimated Cost: ${multi_agent_cost['estimated_cost']:.4f}"
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
                with st.spinner(f"Processing with {st.session_state.get('num_analysis_agents', 1)} agents..."):
                    if len(chunks) == 1 and st.session_state.get('num_analysis_agents', 1) > 1:
                        # Process with multiple agents
                        agent_summaries = []
                        for i in range(st.session_state.num_analysis_agents):
                            agent_summary = process_chunk_with_agent(
                                edited_chunk,
                                1,
                                1,
                                model,
                                api_key,
                                provider,
                                agent_id=i+1
                            )
                            agent_summaries.append(agent_summary)
                            # Show individual agent progress
                            st.info(f"Agent {i+1} analysis complete")
                        
                        # Merge agent summaries with coordinator
                        final_analysis = merge_summaries_with_coordinator(
                            agent_summaries,
                            model,
                            api_key,
                            provider
                        )
                        
                        # Add final consensus to chat without the waiting message
                        consensus_msg = (
                            f"**Multi-Agent Analysis Consensus** (from {len(agent_summaries)} agents):\n\n"
                            f"{final_analysis}"
                        )
                        # Use show_message=True but is_chunk=False to avoid the waiting message
                        process_chat_message(consensus_msg, show_message=True, is_chunk=False)
                    else:
                        # Original single-agent processing
                        for i, chunk in enumerate(chunks, 1):
                            chunk_content = f"[Chunk {i}/{len(chunks)}]\n{chunk}"
                            if i == 1:
                                process_chat_message(edited_chunk, show_message=True, is_chunk=True)
                            else:
                                process_chat_message(chunk_content, show_message=True, is_chunk=True)
                            time.sleep(0.5)
                    
                    # After all processing is complete
                    process_chat_message(
                        "Analysis complete. You may now ask questions about the codebase.",
                        show_message=False
                    )
                    del st.session_state.pending_prompt_chunks
                    st.rerun()
        with col1:
            if st.button("Clear", use_container_width=True):
                del st.session_state.pending_prompt_chunks
                if 'num_analysis_agents' in st.session_state:
                    del st.session_state.num_analysis_agents
                st.rerun()
    # Regular chat input if no pending prompt
    else:
        # Add Deep Think mode configuration
        with st.expander("🧠 Deep Think Settings", expanded=False):
            use_deep_think = st.toggle("Enable Deep Think Mode", value=False, 
                help="Use multiple agents to analyze your question and synthesize a comprehensive answer")
            
            if use_deep_think:
                num_agents = st.slider(
                    "Number of Thinking Agents",
                    min_value=2,
                    max_value=25,
                    value=3,
                    help="How many agents should independently analyze and answer before reaching consensus"
                )
                st.session_state.deep_think_agents = num_agents
            else:
                if 'deep_think_agents' in st.session_state:
                    del st.session_state.deep_think_agents

            # Add DeepSeek temperature settings if DeepSeek is selected
            provider = st.session_state.config.get('llm_provider')
            if provider == "DeepSeek":
                st.markdown("#### DeepSeek Temperature Settings")
                use_case = st.selectbox(
                    "Select Use Case",
                    options=[
                        "Coding / Math",
                        "Data Cleaning / Analysis",
                        "General Conversation",
                        "Translation",
                        "Creative Writing"
                    ],
                    help="Different use cases work better with different temperature settings"
                )
                
                # Show the corresponding temperature
                temperatures = {
                    "Coding / Math": 0.0,
                    "Data Cleaning / Analysis": 1.0,
                    "General Conversation": 1.3,
                    "Translation": 1.3,
                    "Creative Writing": 1.5
                }
                
                selected_temp = temperatures[use_case]
                st.info(f"Recommended temperature for {use_case}: {selected_temp}")
                
                # Allow manual override
                custom_temp = st.slider(
                    "Custom Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=selected_temp,
                    step=0.1,
                    help="Higher values = more creative, Lower values = more precise"
                )
                
                # Store in session state
                st.session_state.config['deepseek_temperature'] = custom_temp

        # Token analysis section between settings and chat
        analysis_container = st.container()
        
        # Get provider and model before chat input
        provider = st.session_state.config.get('llm_provider')
        model = st.session_state.config.get('model')
        
        # Check if any provider has keys configured
        any_provider_configured = False
        for provider_info in SidebarComponent.LLM_PROVIDERS.values():
            key_name = provider_info["key_name"]
            keys = st.session_state.config.get('api_keys', {}).get(key_name, [])
            if not isinstance(keys, list):
                keys = [keys] if keys else []
            if keys:
                any_provider_configured = True
                break

        # Get API key with rotation for current provider
        api_key = get_api_key(provider)
        if not api_key and not any_provider_configured:
            st.error("Please configure at least one API key in the settings to use the chat.")
            return
        elif not api_key:
            # If current provider has no key but others do, suggest switching
            st.warning(f"No API key configured for {provider}. Please select a different provider in the settings.")
            return
        
        # Create a text input for real-time analysis
        if 'current_input' not in st.session_state:
            st.session_state.current_input = ""
            
        current_text = st.text_area("Type your message here...", 
            value=st.session_state.current_input,
            key="message_input",
            height=100)
            
        # Update analysis whenever text changes
        if current_text != st.session_state.current_input:
            st.session_state.current_input = current_text
            
        if current_text:
            with analysis_container:
                token_metrics = estimate_token_cost([current_text], provider, model)
                
                # Display token analysis in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Input Tokens", f"{token_metrics['input_tokens']:,}")
                with col2:
                    st.metric("Output Tokens (est.)", f"{token_metrics['output_tokens']:,}")
                with col3:
                    st.metric("Single Response Cost", f"${token_metrics['estimated_cost']:.4f}")
                
                # Deep Think cost estimation if enabled
                if use_deep_think:
                    deep_think_metrics = estimate_token_cost(
                        [current_text] * num_agents,
                        provider,
                        model
                    )
                    st.warning(
                        f"Deep Think Total Cost ({num_agents} agents + synthesis):\n"
                        f"${deep_think_metrics['estimated_cost']:.4f}"
                    )
        
        # Add send button
        if st.button("Send", use_container_width=True):
            if current_text:
                if use_deep_think:
                    with st.spinner(f" Deep thinking with {num_agents} agents..."):
                        # Run async analysis in event loop
                        consensus = asyncio.run(
                            run_deep_think_analysis(
                                current_text,
                                model,
                                api_key,
                                provider,
                                num_agents
                            )
                        )
                        
                        # Add consensus to chat
                        consensus_msg = (
                            f"**Deep Think Analysis** (from {num_agents} parallel agents):\n\n"
                            f"{consensus}"
                        )
                        process_chat_message(consensus_msg, show_message=True)
                else:
                    # Regular single-agent processing
                    process_chat_message(current_text, show_message=True)
                
                # Clear input after sending
                st.session_state.current_input = ""
                st.rerun()

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

def process_chunk_with_agent(chunk: str, chunk_num: int, total_chunks: int, model: str, api_key: str, provider: str, agent_id: int = None) -> dict:
    """Process a single chunk with a summarizer agent."""
    system_prompt = f"""You are code analysis agent{f' #{agent_id}' if agent_id else ''} responsible for analyzing code. Your task is to:
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
   - cross_references: References to elements that might appear in other chunks
   - agent_id: {agent_id if agent_id else 'null'} (for multi-agent analysis)"""

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
    try:
        if provider == "DeepSeek":
            # Use synthesize_insights for DeepSeek which handles the API correctly
            temperature = st.session_state.config.get('deepseek_temperature', 0.0)
            return asyncio.run(synthesize_insights(summaries, api_key, temperature))
            
        # Check if Gemini is configured as coordinator
        gemini_config = SidebarComponent.LLM_PROVIDERS.get("Gemini", {})
        if gemini_config.get("is_coordinator") and "GEMINI_API_KEY" in st.session_state.config.get('api_keys', {}):
            return merge_summaries_with_gemini(
                summaries,
                st.session_state.config['api_keys']['GEMINI_API_KEY']
            )
            
        # For other providers, use existing logic
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

def get_deepseek_temperature(context_type: str = "coding") -> float:
    """Get the recommended temperature for DeepSeek based on context type."""
    temperatures = {
        "coding": 0.0,      # Coding and math tasks
        "data": 1.0,        # Data cleaning and analysis
        "conversation": 1.3, # General conversation
        "translation": 1.3,  # Translation tasks
        "creative": 1.5     # Creative writing and poetry
    }
    return temperatures.get(context_type, 1.0)  # Default to data/analysis temperature

def create_deepseek_client(api_key: str, is_async: bool = False, use_openai_client: bool = False):
    """Create a DeepSeek client using either the OpenAI client or raw implementation."""
    if use_openai_client:
        from openai import OpenAI, AsyncOpenAI
        if is_async:
            return AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        return OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
    return api_key  # Original behavior for raw implementation

async def raw_deepseek_request(messages: list, api_key: str, temperature: float = 1.0):
    """Make a raw HTTP request to DeepSeek API using aiohttp."""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature,
        "stream": False,  # Force non-streaming mode
        "max_tokens": 2048  # Reasonable limit to prevent timeouts
    }
    
    timeout = aiohttp.ClientTimeout(total=120)  # 2 minute total timeout
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            logger.info(f"Starting DeepSeek request to {url}")
            start_time = time.time()
            
            async with session.post(url, headers=headers, json=payload) as resp:
                elapsed = time.time() - start_time
                logger.info(f"DeepSeek response received in {elapsed:.2f}s with status {resp.status}")
                
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"DeepSeek error response: {text}")
                    raise RuntimeError(f"DeepSeek returned status {resp.status}: {text}")
                
                data = await resp.json()
                logger.debug(f"DeepSeek response parsed successfully")
                return data
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"DeepSeek request timed out after {elapsed:.2f}s")
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"DeepSeek request failed after {elapsed:.2f}s: {str(e)}")
            raise

async def process_deepseek_request(messages: list, api_key: str, temperature: float = 1.0) -> str:
    """Process a DeepSeek request with retries and error handling."""
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            start_time = time.time()
            logger.info(f"DeepSeek request attempt {attempt + 1}/{MAX_RETRIES + 1}")
            
            data = await raw_deepseek_request(messages, api_key, temperature)
            
            # Extract and log token usage if available
            if "usage" in data:
                usage = data["usage"]
                logger.info(
                    f"Token usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                    f"Completion: {usage.get('completion_tokens', 0)}, "
                    f"Total: {usage.get('total_tokens', 0)}"
                )
            
            # Check for and log cache information
            if "cache_info" in data:
                cache = data["cache_info"]
                logger.info(f"Cache info - Hit: {cache.get('hit', False)}")
            
            # Extract the response content
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                elapsed = time.time() - start_time
                logger.info(f"DeepSeek request successful in {elapsed:.2f}s")
                return content
            else:
                raise ValueError("No content in DeepSeek response")
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"DeepSeek request failed (attempt {attempt + 1}/{MAX_RETRIES + 1}). "
                f"Error: {str(e)}. Elapsed: {elapsed:.2f}s"
            )
            
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY}s...")
                await asyncio.sleep(RETRY_DELAY)
                continue
            else:
                logger.error("All DeepSeek request attempts failed")
                raise

def process_chat_message(prompt: str, show_message: bool = True, is_chunk: bool = False):
    """Process a chat message and get LLM response."""
    # Don't process empty messages
    if not prompt.strip():
        return

    # Get API configuration
    provider = st.session_state.config.get('llm_provider')
    model = st.session_state.config.get('model')
    
    # Get API key with rotation
    api_key = get_api_key(provider)
    if not api_key:
        st.error(f"Please configure at least one {provider} API key in the settings first.")
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
            # Get the last non-chunk assistant message (final analysis)
            final_analysis = None
            for msg in reversed(st.session_state.messages):
                if msg["role"] == "assistant" and "Analyzing chunk" not in msg["content"]:
                    final_analysis = msg
                    break
            
            # Prepare messages for API
            messages_for_api = [
                st.session_state.messages[0],  # System message
            ]
            
            # Add final analysis if available
            if final_analysis:
                messages_for_api.append(final_analysis)
            
            # Add current question
            messages_for_api.append({"role": "user", "content": prompt})

            # Get response from selected provider
            if provider == "OpenAI":
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=messages_for_api,
                    timeout=60
                )
                assistant_response = response.choices[0].message.content
            elif provider == "Anthropic":
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=model,
                    messages=messages_for_api,
                    timeout=60
                )
                assistant_response = response.content[0].text
            elif provider == "DeepSeek":
                temperature = st.session_state.config.get('deepseek_temperature', 1.0)
                
                # Use the new direct aiohttp implementation
                async def run_deepseek():
                    return await process_deepseek_request(messages_for_api, api_key, temperature)
                
                # Run the async function
                assistant_response = asyncio.run(run_deepseek())
            else:
                st.error(f"Provider {provider} not yet implemented")
                return

            if show_message:
                st.markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            error_msg = f"Error calling {provider} API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            # Add error message to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ {error_msg}\n\nPlease try again or regenerate the codebase analysis."
            })

def render_codebase_view():
    """Render the codebase overview."""
    from frontend.codebase_view import render_codebase_view as render_parser_view
    render_parser_view()

def render_dashboard():
    """Render the main dashboard."""
    try:
        initialize_torch()
    except Exception as e:
        logger.warning(f"PyTorch initialization warning (non-critical): {str(e)}")
    
    # Get sidebar component and render it
    sidebar = SidebarComponent()
    repo_path = sidebar.render()

    # Initialize active tab if not set
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "LLM Chat"  # Default to chat tab

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

def get_provider_costs(provider: str, model: str) -> dict:
    """Get token costs for a specific provider and model."""
    costs = {
        'OpenAI': {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002}
        },
        'Anthropic': {
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
        },
        'DeepSeek': {
            'deepseek-chat': {'input': 0.002, 'output': 0.002}
        }
    }
    return costs.get(provider, {}).get(model, {'input': 0.002, 'output': 0.002})

def estimate_token_cost(chunks: list, provider: str, model: str) -> dict:
    """Estimate token usage and cost for processing chunks with multi-agent system."""
    from backend.core.tokenizer import TokenCalculator
    
    calculator = TokenCalculator()
    total_input_tokens = sum(calculator.count_tokens(chunk, model)[0] for chunk in chunks)
    
    # Token estimates for processing stages
    summarizer_tokens = {
        'input': total_input_tokens + 300,  # System prompt overhead
        'output': 500  # Average summary size
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
    
    # Get costs for provider/model
    rates = get_provider_costs(provider, model)
    estimated_cost = (
        (total_tokens['input'] / 1000) * rates['input'] +
        (total_tokens['output'] / 1000) * rates['output']
    )
    
    return {
        'total_tokens': sum(total_tokens.values()),
        'input_tokens': total_tokens['input'],
        'output_tokens': total_tokens['output'],
        'estimated_cost': round(estimated_cost, 4),
        'model': model
    }

class DistributedCognitionSystem:
    """A system that coordinates specialized agents with persistent memory to simulate higher intelligence."""
    
    def __init__(self, persist_dir: str = "./cognitive_memory"):
        self.persist_dir = persist_dir
        self._memory = None
        self._collection = None
        self._embedding_fn = None
        self._initialize_roles()
    
    @property
    def memory(self):
        """Lazy initialization of ChromaDB client."""
        if self._memory is None:
            import os
            os.makedirs(self.persist_dir, exist_ok=True)
            
            self._memory = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._memory
    
    @property
    def embedding_fn(self):
        """Lazy initialization of embedding function."""
        if self._embedding_fn is None:
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        return self._embedding_fn
    
    @property
    def collection(self):
        """Lazy initialization of collection."""
        if self._collection is None:
            self._collection = self.memory.get_or_create_collection(
                name="agent_insights",
                embedding_function=self.embedding_fn
            )
        return self._collection

    def _initialize_roles(self):
        """Initialize specialized agent roles."""
        self.agent_roles = {
            0: "Delegator - Analyzes tasks and coordinates specialist selection",
            1: "Technical Architect - Focus on system design and architecture patterns",
            2: "Implementation Specialist - Focus on concrete code and implementation details",
            3: "Security Analyst - Focus on security implications and best practices",
            4: "Performance Expert - Focus on optimization and scalability",
            5: "Integration Specialist - Focus on system interactions and dependencies",
            6: "Data Flow Analyst - Focus on data structures and transformations",
            7: "Error Handling Specialist - Focus on robustness and recovery",
            8: "Testing Strategist - Focus on test coverage and validation",
            9: "Documentation Expert - Focus on code clarity and maintainability",
            10: "API Designer - Focus on interface design and contracts",
            11: "Concurrency Specialist - Focus on parallel processing and race conditions",
            12: "Memory Management Expert - Focus on resource utilization",
            13: "Code Quality Analyst - Focus on best practices and patterns",
            14: "Dependency Analyst - Focus on external integrations",
            15: "Configuration Specialist - Focus on system settings and env vars",
            16: "Logging Expert - Focus on observability and debugging",
            17: "State Management Analyst - Focus on data consistency",
            18: "UI/UX Specialist - Focus on user interaction patterns",
            19: "Database Expert - Focus on data persistence and queries",
            20: "Cache Specialist - Focus on performance optimization",
            21: "Network Analyst - Focus on communication patterns",
            22: "Authentication Expert - Focus on access control",
            23: "Deployment Specialist - Focus on CI/CD and automation",
            24: "Monitoring Expert - Focus on system health and metrics",
            25: "Compliance Analyst - Focus on regulatory requirements"
        }
    
    def get_agent_role(self, agent_id: int) -> str:
        """Get the role description for a specific agent ID."""
        return self.agent_roles.get(agent_id, "General Analyst")
    
    def store_insight(self, content: str, metadata: dict):
        """Store an agent's insight with metadata for future retrieval."""
        try:
            # Only initialize collection when needed
            if not content:  # Skip empty content
                return
                
            # Generate ID based on timestamp and agent_id if present
            insight_id = f"insight_{time.time()}"
            if 'agent_id' in metadata:
                insight_id += f"_{metadata['agent_id']}"
            
            # Clean and validate metadata for ChromaDB
            clean_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, (list, dict)):
                    clean_metadata[k] = str(v)
                elif v is None:
                    clean_metadata[k] = "none"
                else:
                    clean_metadata[k] = str(v)
            
            clean_metadata.setdefault("type", "unknown")
            clean_metadata.setdefault("timestamp", str(time.time()))
            
            # Add document to collection
            self.collection.add(
                documents=[content],
                metadatas=[clean_metadata],
                ids=[insight_id]
            )
            logger.debug(f"Stored insight {insight_id}")
            
        except Exception as e:
            logger.error(f"Error storing insight: {str(e)}")
            pass  # Continue execution even if storage fails
    
    def retrieve_relevant_insights(self, query: str, top_k: int = 5) -> list:
        """Retrieve most relevant past insights for a given query."""
        try:
            # Skip if no query
            if not query:
                return []
                
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            return results['documents'][0]  # Return top matches
        except Exception as e:
            logger.error(f"Error retrieving insights: {str(e)}")
            return []  # Return empty list on error

    async def analyze_task_requirements(self, prompt: str, model: str, api_key: str, provider: str) -> list[tuple[int, str, str]]:
        """
        Uses the Delegator agent to analyze a prompt and determine required specialists.
        Returns list of tuples: (agent_id, provider, model)
        """
        # Prepare system prompt for delegator
        system_prompt = """You are the Delegator agent responsible for analyzing tasks and selecting the most appropriate specialist team.
        
Available specialists:
{}

Provider Strengths:
- GPT-4: Excels at finding bugs, code review, security analysis, and error handling
- Claude-3 Sonnet: Excels at code generation, implementation details, architecture design, and documentation
- Gemini: Good for coordination and synthesis
- DeepSeek: Good for specific domain tasks

Your task is to:
1. Analyze the given prompt/task
2. Identify key aspects that require specialist attention
3. Select 3-5 most relevant specialists and assign them the most appropriate provider based on the task
4. Explain why each specialist and provider combination was chosen

Format your response as:
SELECTED_SPECIALISTS:
- ID: [id], Provider: [provider], Model: [model] - Reason: [explanation]

Example:
SELECTED_SPECIALISTS:
- ID: 3, Provider: OpenAI, Model: gpt-4 - Reason: Security analysis requires GPT-4's strength in finding edge cases
- ID: 2, Provider: Anthropic, Model: claude-3-sonnet - Reason: Implementation requires Claude's code generation capabilities
""".format("\n".join(f"{id}: {role}" for id, role in self.agent_roles.items() if id != 0))

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response_content = None
            # Use Gemini as the delegator if available
            if "GEMINI_API_KEY" in st.session_state.config.get('api_keys', {}):
                import google.generativeai as genai
                genai.configure(api_key=st.session_state.config['api_keys']['GEMINI_API_KEY'])
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                chat = model.start_chat(history=[])
                response = chat.send_message(
                    f"{system_prompt}\n\n{prompt}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        top_p=0.8,
                        top_k=40
                    )
                )
                response_content = response.text
            else:
                # Fallback to original provider if Gemini not available
                if provider == "OpenAI":
                    from openai import AsyncOpenAI
                    client = AsyncOpenAI(api_key=api_key)
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        timeout=30
                    )
                    response_content = response.choices[0].message.content
                elif provider == "Anthropic":
                    from anthropic import AsyncAnthropic
                    client = AsyncAnthropic(api_key=api_key)
                    response = await client.messages.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        timeout=30
                    )
                    response_content = response.content[0].text

            if response_content:
                # Parse response to extract selected specialist IDs and their providers
                try:
                    import re
                    specialists = []
                    # Look for entries in format: ID: X, Provider: Y, Model: Z
                    pattern = r'ID:\s*(\d+),\s*Provider:\s*(\w+),\s*Model:\s*([\w-]+)'
                    matches = re.finditer(pattern, response_content)
                    
                    for match in matches:
                        agent_id = int(match.group(1))
                        provider = match.group(2)
                        model = match.group(3)
                        
                        # Validate agent_id and provider
                        if 0 < agent_id <= len(self.agent_roles) and provider in SidebarComponent.LLM_PROVIDERS:
                            specialists.append((agent_id, provider, model))
                    
                    if specialists:
                        return specialists[:5]  # Limit to max 5 specialists
                        
                except Exception as e:
                    logger.error(f"Error parsing delegator response: {str(e)}")
                    
            # Fallback to default selection if parsing fails
            return [
                (1, "Anthropic", "claude-3-sonnet"),  # Technical Architect with Claude
                (2, "Anthropic", "claude-3-sonnet"),  # Implementation with Claude
                (3, "OpenAI", "gpt-4")  # Security with GPT-4
            ]
            
        except Exception as e:
            logger.error(f"Error in delegator analysis: {str(e)}")
            return [
                (1, "Anthropic", "claude-3-sonnet"),
                (2, "Anthropic", "claude-3-sonnet"),
                (3, "OpenAI", "gpt-4")
            ]

async def process_deep_think_agent_async(prompt: str, model: str, api_key: str, provider: str, agent_id: int, 
                                       cognitive_system: DistributedCognitionSystem = None) -> str:
    """Enhanced async agent with specialized roles and access to collective memory."""
    
    # Define specialized agent roles as fallback
    agent_roles = {
        1: "Technical Architect - Focus on system design and architecture patterns",
        2: "Implementation Specialist - Focus on concrete code and implementation details",
        3: "Security Analyst - Focus on security implications and best practices",
        4: "Performance Expert - Focus on optimization and scalability",
        5: "Integration Specialist - Focus on system interactions and dependencies",
        6: "Data Flow Analyst - Focus on data structures and transformations",
        7: "Error Handling Specialist - Focus on robustness and recovery",
        8: "Testing Strategist - Focus on test coverage and validation",
        9: "Documentation Expert - Focus on code clarity and maintainability",
        10: "API Designer - Focus on interface design and contracts",
        11: "Concurrency Specialist - Focus on parallel processing and race conditions",
        12: "Memory Management Expert - Focus on resource utilization",
        13: "Code Quality Analyst - Focus on best practices and patterns",
        14: "Dependency Analyst - Focus on external integrations",
        15: "Configuration Specialist - Focus on system settings and env vars",
        16: "Logging Expert - Focus on observability and debugging",
        17: "State Management Analyst - Focus on data consistency",
        18: "UI/UX Specialist - Focus on user interaction patterns",
        19: "Database Expert - Focus on data persistence and queries",
        20: "Cache Specialist - Focus on performance optimization",
        21: "Network Analyst - Focus on communication patterns",
        22: "Authentication Expert - Focus on access control",
        23: "Deployment Specialist - Focus on CI/CD and automation",
        24: "Monitoring Expert - Focus on system health and metrics",
        25: "Compliance Analyst - Focus on regulatory requirements"
    }
    
    # Get agent's specialized role (use cognitive system if available, otherwise fallback to local roles)
    agent_role = cognitive_system.get_agent_role(agent_id) if cognitive_system else agent_roles.get(agent_id, f"Agent #{agent_id}")
    
    # Retrieve different types of relevant insights
    relevant_insights = {
        "role_specific": [],  # Insights specific to this agent's role
        "task_specific": [],  # Insights related to the current task
        "general": []         # Generally relevant insights
    }
    
    if cognitive_system:
        # Get role-specific insights by focusing on this agent's specialty
        role_query = f"{agent_role} analysis for: {prompt}"
        relevant_insights["role_specific"] = cognitive_system.retrieve_relevant_insights(
            role_query,
            top_k=2
        )
        
        # Get task-specific insights
        relevant_insights["task_specific"] = cognitive_system.retrieve_relevant_insights(
            prompt,
            top_k=2
        )
        
        # Get general insights that might be relevant
        general_query = f"General insights and patterns related to: {prompt}"
        relevant_insights["general"] = cognitive_system.retrieve_relevant_insights(
            general_query,
            top_k=1
        )

    system_prompt = f"""You are deep thinking agent #{agent_id}, specializing as a {agent_role}. 
Your task is to analyze the problem from your specialist perspective while leveraging collective knowledge.

Role-Specific Past Insights (from your specialty area):
{chr(10).join(relevant_insights["role_specific"]) if relevant_insights["role_specific"] else "No role-specific insights available."}

Task-Specific Past Insights (directly related to current task):
{chr(10).join(relevant_insights["task_specific"]) if relevant_insights["task_specific"] else "No task-specific insights available."}

General Relevant Insights:
{chr(10).join(relevant_insights["general"]) if relevant_insights["general"] else "No general insights available."}

Your analysis should:
1. Build upon relevant past insights
2. Focus deeply on your specialty ({agent_role})
3. Consider how your analysis complements other specialists
4. Provide concrete, actionable recommendations
5. Include code examples or technical specifics where relevant

Format your response with clear sections:
- Key Insights (from your specialty perspective)
- Technical Details
- Recommendations
- Integration Points (how your insights connect with other specialties)"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response_content = None
        if provider == "OpenAI":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=60
            )
            response_content = response.choices[0].message.content
        elif provider == "Anthropic":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model=model,
                messages=messages,
                timeout=60
            )
            response_content = response.content[0].text
        elif provider == "DeepSeek":
            client = create_deepseek_client(api_key, is_async=True)
            temperature = st.session_state.config.get('deepseek_temperature', 1.0)
            response_content = await process_deepseek_request(messages, api_key, temperature)
            
        # Store the insight with enhanced metadata
        if cognitive_system and response_content:
            cognitive_system.store_insight(
                response_content,
                {
                    "type": "agent_response",
                    "role": agent_role,
                    "agent_id": str(agent_id),  # Convert to string
                    "timestamp": time.time(),
                    "prompt": prompt,
                    "role_specific_insights": len(relevant_insights["role_specific"]),  # Use primitive types
                    "task_specific_insights": len(relevant_insights["task_specific"]),
                    "general_insights": len(relevant_insights["general"])
                }
            )
            
        return response_content
    except Exception as e:
        logger.error(f"Error in deep think agent: {str(e)}")
        return f"Error in agent #{agent_id}: {str(e)}"

async def run_deep_think_analysis(prompt: str, model: str, api_key: str, provider: str, num_agents: int):
    """Run parallel analysis with proper async handling."""
    
    # Initialize cognitive system if not exists
    if 'cognitive_system' not in st.session_state:
        st.session_state.cognitive_system = DistributedCognitionSystem()
    
    try:
        progress_placeholder = st.empty()
        
        # Get all available API keys first
        available_providers = {}
        for provider_name, provider_info in SidebarComponent.LLM_PROVIDERS.items():
            key_name = provider_info["key_name"]
            keys = st.session_state.config.get('api_keys', {}).get(key_name, [])
            if not isinstance(keys, list):
                keys = [keys] if keys else []
            if keys:
                available_providers[provider_name] = {
                    "models": provider_info["models"],
                    "keys": keys,
                    "is_coordinator": provider_info.get("is_coordinator", False)
                }
        
        if not available_providers:
            return "Error: No API keys configured. Please add at least one API key in the settings."
            
        progress_placeholder.markdown("🤖 Analyzing available providers and assigning roles...")
        
        # Let delegator analyze and select specialists with their providers
        selected_specialists = await st.session_state.cognitive_system.analyze_task_requirements(
            prompt, model, api_key, provider
        )
        
        # Filter specialists based on available providers
        filtered_specialists = []
        for agent_id, agent_provider, agent_model in selected_specialists:
            if agent_provider in available_providers:
                filtered_specialists.append((agent_id, agent_provider, agent_model))
        
        if not filtered_specialists:
            # Fall back to using whatever providers we have
            available_provider = next(iter(available_providers.items()))[0]
            available_model = available_providers[available_provider]["models"][0]
            filtered_specialists = [(1, available_provider, available_model)]
        
        # Show which roles and providers were selected
        role_displays = []
        for i, (agent_id, agent_provider, agent_model) in enumerate(filtered_specialists):
            role = st.session_state.cognitive_system.get_agent_role(agent_id)
            role_displays.append(f"🤖 Agent {i+1}: {role} (using {agent_provider} - {agent_model})")
        
        roles_display = "\n".join(role_displays)
        progress_placeholder.markdown(
            f"""### Selected Analysis Team:
{roles_display}

*Running analysis with specialized agents...*"""
        )
        
        # Create tasks for specialized agents
        tasks = []
        for agent_id, agent_provider, agent_model in filtered_specialists:
            # Get provider-specific API key
            agent_api_key = get_api_key(agent_provider)
            if not agent_api_key:
                continue
                
            task = process_deep_think_agent_async(
                prompt, 
                agent_model,
                agent_api_key,
                agent_provider,
                agent_id,
                st.session_state.cognitive_system
            )
            tasks.append(task)
        
        if not tasks:
            return "Error: No agents could be initialized. Please check API key configuration."
        
        # Run all agents in parallel with timeout
        agent_responses = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=90
        )
        
        # Update progress
        progress_placeholder.markdown("✨ Analysis complete! Synthesizing insights...")
        
        # Merge insights using the best available coordinator
        coordinator_provider = None
        for provider_name, info in available_providers.items():
            if info.get("is_coordinator"):
                coordinator_provider = provider_name
                break
        
        if coordinator_provider == "Gemini" and "GEMINI_API_KEY" in st.session_state.config.get('api_keys', {}):
            final_analysis = merge_summaries_with_gemini(
                agent_responses,
                st.session_state.config['api_keys']['GEMINI_API_KEY']
            )
        else:
            # Use DeepSeek or fallback to original provider
            if "DeepSeek" in available_providers:
                final_analysis = await synthesize_insights(
                    agent_responses,
                    get_api_key("DeepSeek"),
                    st.session_state.config.get('deepseek_temperature', 0.0)
                )
            else:
                final_analysis = merge_summaries_with_coordinator(
                    agent_responses, model, api_key, provider
                )
        
        return final_analysis
        
    except asyncio.TimeoutError:
        return "Analysis timed out. Please try again or reduce the number of agents."
    except Exception as e:
        logger.error(f"Error in deep think analysis: {str(e)}")
        return f"Error during analysis: {str(e)}"

async def merge_deep_think_responses(responses: list, original_prompt: str, model: str, api_key: str, provider: str, 
                             cognitive_system: DistributedCognitionSystem = None) -> str:
    """Merge responses with comprehensive stages and refined coordination."""
    
    try:
        logger.info("Starting enhanced synthesis process...")
        progress_placeholder = st.empty()
        progress_placeholder.text("Starting comprehensive synthesis...")
        
        # Store all agent responses first
        logger.info(f"Storing {len(responses)} agent responses")
        for i, response in enumerate(responses):
            cognitive_system.store_insight(
                response,
                {
                    "type": "agent_response",
                    "timestamp": time.time(),
                    "prompt": original_prompt
                }
            )
        
        # Enhanced multi-stage processing pipeline
        stages = [
            {"name": "Technical Analysis", "query": f"Technical implementation details for: {original_prompt}"},
            {"name": "Architecture Patterns", "query": f"System design patterns and architecture for: {original_prompt}"},
            {"name": "Integration Points", "query": f"System integration and connection points for: {original_prompt}"},
            {"name": "Implementation Strategy", "query": f"Step-by-step implementation guide for: {original_prompt}"},
            {"name": "Potential Pitfalls", "query": f"Common pitfalls, edge cases, and solutions for: {original_prompt}"},
            {"name": "Testing Strategy", "query": f"Testing approach and validation methods for: {original_prompt}"},
            {"name": "Performance Considerations", "query": f"Performance optimization strategies for: {original_prompt}"},
            {"name": "Security Implications", "query": f"Security considerations and best practices for: {original_prompt}"},
            {"name": "Example Usage", "query": f"Practical examples and code snippets for: {original_prompt}"}
        ]
        
        stage_insights = []
        for stage in stages:
            try:
                progress_placeholder.text(f"Processing {stage['name']}...")
                logger.info(f"Starting {stage['name']} stage")
                
                # Get insights for this stage
                relevant_insights = {
                    "stage_specific": cognitive_system.retrieve_relevant_insights(
                        stage["query"], 
                        top_k=2
                    ),
                    "cross_stage": cognitive_system.retrieve_relevant_insights(
                        f"Connections between {stage['name']} and other aspects of: {original_prompt}",
                        top_k=2
                    ),
                    "implementation": cognitive_system.retrieve_relevant_insights(
                        f"Implementation details and code examples for {stage['name']} in: {original_prompt}",
                        top_k=1
                    )
                }
                
                # Enhanced stage prompt template
                stage_prompt = f"""As a specialized {stage['name']} expert, create a detailed analysis focusing on:

1. Comprehensive Overview
2. Detailed Implementation Steps
3. Best Practices and Guidelines
4. Practical Examples (with code snippets if applicable)
5. Common Challenges and Solutions

Consider these relevant insights:

Stage-Specific Past Insights:
{chr(10).join(relevant_insights["stage_specific"])}

Cross-Stage Connections:
{chr(10).join(relevant_insights["cross_stage"])}

Implementation Examples:
{chr(10).join(relevant_insights["implementation"])}

Format your response with clear sections, bullet points, and code blocks where appropriate."""
                
                # Create focused messages
                messages = [
                    {
                        "role": "system",
                        "content": stage_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Provide a detailed {stage['name'].lower()} analysis for: {original_prompt}"
                    }
                ]
                
                # Process stage with timeout
                if provider == "DeepSeek":
                    temperature = st.session_state.config.get('deepseek_temperature', 0.7)
                    stage_response = await process_deepseek_request(messages, api_key, temperature)
                    stage_insights.append(f"### {stage['name']}\n{stage_response}")
                    
                    # Store stage result
                    cognitive_system.store_insight(
                        stage_response,
                        {
                            "type": "stage_synthesis",
                            "stage_name": stage["name"],
                            "timestamp": time.time(),
                            "prompt": original_prompt,
                            "stage_specific_insights": len(relevant_insights["stage_specific"]),
                            "cross_stage_insights": len(relevant_insights["cross_stage"]),
                            "implementation_insights": len(relevant_insights["implementation"])
                        }
                    )
                    logger.info(f"Completed {stage['name']} stage successfully")
                    
            except Exception as e:
                logger.error(f"Error in {stage['name']} stage: {str(e)}")
                stage_insights.append(f"### {stage['name']}\nError: {str(e)}")
                continue
        
        # If we have any successful stage insights, proceed with final synthesis
        if stage_insights:
            progress_placeholder.text("Creating final comprehensive synthesis...")
            logger.info("Starting final synthesis")
            
            final_prompt = """You are the Final Synthesis Coordinator. Your task is to create a comprehensive, 
well-structured technical guide that combines all stage insights into a complete manual.

Your output should follow this structure:

1. Executive Summary
   - Overview of the solution
   - Key technical decisions

2. Technical Architecture
   - System design patterns
   - Component interactions
   - Integration points

3. Implementation Guide
   - Step-by-step instructions
   - Code examples and snippets
   - Configuration requirements

4. Best Practices & Considerations
   - Performance optimization
   - Security measures
   - Error handling
   - Testing strategy

5. Common Challenges
   - Known pitfalls
   - Troubleshooting guide
   - Edge cases

6. Usage Examples
   - Practical scenarios
   - Code samples
   - Expected outcomes

Format the output with clear headings, bullet points, and code blocks.
Ensure all sections are thorough and well-explained."""
            
            final_messages = [
                {
                    "role": "system",
                    "content": final_prompt
                },
                {
                    "role": "user",
                    "content": f"Create a comprehensive technical guide for: {original_prompt}\n\n{chr(10).join(stage_insights)}"
                }
            ]
            
            try:
                if provider == "DeepSeek":
                    temperature = st.session_state.config.get('deepseek_temperature', 0.7)
                    final_response = await process_deepseek_request(final_messages, api_key, temperature)
                    
                    # Simpler refinement prompt
                    refiner_prompt = """Review this technical summary and ensure it is:
1. Clear and focused
2. Properly formatted
3. Free of redundant information
4. Contains specific, actionable items

Keep the structure simple and avoid creating deep nested sections."""
                    
                    refiner_messages = [
                        {"role": "system", "content": refiner_prompt},
                        {"role": "user", "content": f"Review and refine this summary:\n\n{final_response}"}
                    ]
                    
                    refined_response = await process_deepseek_request(refiner_messages, api_key, temperature)
                    
                    # Store final synthesis
                    cognitive_system.store_insight(
                        refined_response,
                        {
                            "type": "final_synthesis",
                            "timestamp": time.time(),
                            "prompt": original_prompt,
                            "num_stage_insights": len(stage_insights),
                            "synthesis_type": "refined"  # Indicate this went through refinement
                        }
                    )
                    
                    logger.info("Final synthesis completed successfully")
                    progress_placeholder.empty()
                    return refined_response
                    
            except Exception as e:
                logger.error(f"Error in final synthesis: {str(e)}")
                progress_placeholder.empty()
                return f"Error in final synthesis. Partial Results:\n\n{chr(10).join(stage_insights)}"
        else:
            logger.error("No successful stage insights to synthesize")
            progress_placeholder.empty()
            return "Error: All synthesis stages failed. Please try again."
            
    except Exception as e:
        logger.error(f"Error in synthesis process: {str(e)}")
        if 'progress_placeholder' in locals():
            progress_placeholder.empty()
        return f"Error in synthesis process: {str(e)}"

async def run_synthesis_stage(stage_name: str, messages: list, api_key: str, temperature: float = 0.0) -> str:
    """Run a synthesis stage with proper error handling."""
    try:
        logger.info(f"Starting {stage_name} stage")
        stage_response = await process_deepseek_request(messages, api_key, temperature)
        return stage_response
    except Exception as e:
        logger.error(f"Error in {stage_name} stage: {str(e)}")
        return None

async def synthesize_insights(insights: list, api_key: str, temperature: float = 0.0) -> str:
    """Synthesize insights from multiple agents into a coherent response."""
    try:
        logger.info("Starting synthesis process...")
        logger.info(f"Storing {len(insights)} agent responses")
        
        # Technical Analysis Stage
        tech_messages = [
            {"role": "system", "content": "You are a technical analyst synthesizing insights about code."},
            {"role": "user", "content": f"Analyze these technical insights and identify key patterns:\n\n{insights}"}
        ]
        tech_analysis = await process_deepseek_request(tech_messages, api_key, temperature)
        if not tech_analysis:
            return "Error in technical analysis stage"
            
        # Architecture Patterns Stage
        arch_messages = [
            {"role": "system", "content": "You are an architect identifying architectural patterns."},
            {"role": "user", "content": f"Based on this technical analysis, what architectural patterns emerge?\n\n{tech_analysis}"}
        ]
        arch_patterns = await process_deepseek_request(arch_messages, api_key, temperature)
        if not arch_patterns:
            return "Error in architecture patterns stage"
            
        # Integration Points Stage
        integration_messages = [
            {"role": "system", "content": "You are an integration specialist identifying connection points."},
            {"role": "user", "content": f"Given these patterns, what are the key integration points?\n\n{arch_patterns}"}
        ]
        integration_points = await process_deepseek_request(integration_messages, api_key, temperature)
        if not integration_points:
            return "Error in integration points stage"
            
        # Final Synthesis Stage
        final_messages = [
            {"role": "system", "content": "You are a solution architect creating final recommendations."},
            {"role": "user", "content": f"""Synthesize a final recommendation based on:
                Technical Analysis: {tech_analysis}
                Architecture Patterns: {arch_patterns}
                Integration Points: {integration_points}"""}
        ]
        final_response = await process_deepseek_request(final_messages, api_key, temperature)
        return final_response
            
    except Exception as e:
        logger.error(f"Error in synthesis: {str(e)}")
        return f"Error in synthesis: {str(e)}" 

def merge_summaries_with_gemini(summaries: list[str], gemini_api_key: str) -> str:
    """
    Takes a list of partial 'summaries' from specialized agents
    and calls Gemini 1.5 to produce a single, well-structured final analysis.
    """
    import google.generativeai as genai
    from time import sleep
    
    try:
        # Get single API key if it's a list
        if isinstance(gemini_api_key, list):
            if not gemini_api_key:
                raise ValueError("No Gemini API key available")
            gemini_api_key = gemini_api_key[0]
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        
        # Build system instruction
        system_instruction = (
            "You are a coordination agent responsible for synthesizing multiple code-chunk summaries "
            "into a coherent final analysis. Your task is to:\n"
            "1. Review all chunk summaries\n"
            "2. Identify and connect related components across chunks\n"
            "3. Resolve any conflicts or inconsistencies\n"
            "4. Create a comprehensive but concise final analysis that:\n"
            "   - Maintains crucial technical details\n"
            "   - Explains the overall architecture\n"
            "   - Highlights important relationships\n"
            "   - Preserves specific implementation details\n\n"
            "Your response should be clear, well-structured, and ready to be presented to the user.\n"
        )

        # Initialize model with system instruction
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-001",
            system_instruction=system_instruction
        )

        # Format agent outputs into content
        content = "Here are partial summaries from specialized agents:\n\n"
        for i, summary in enumerate(summaries, start=1):
            content += f"---\n**Agent {i} Summary**:\n{summary}\n"
        content += (
            "\nPlease merge these into one final, cohesive analysis. "
            "Add headings, bullet points, code examples, or anything needed for clarity.\n"
        )

        # Create generation config
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.8,
            top_k=40,
            max_output_tokens=4096
        )

        # Send request with retry logic
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                response = model.generate_content(
                    content,
                    generation_config=generation_config
                )
                
                if response.prompt_feedback.block_reason:
                    logger.warning(f"Response blocked: {response.prompt_feedback.block_reason}")
                    return "Response was blocked due to content safety filters. Please try again with different content."
                
                return response.text
                
            except Exception as e:
                if "429" in str(e) and attempt < MAX_RETRIES - 1:  # Rate limit error
                    sleep(2 ** attempt)  # Exponential backoff
                    continue
                elif attempt == MAX_RETRIES - 1:
                    logger.error(f"All Gemini coordination attempts failed: {str(e)}")
                    raise
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"Error in Gemini coordinator: {str(e)}")
        return f"Error synthesizing with Gemini: {str(e)}"

def get_api_key(provider: str) -> Optional[str]:
    """Get an API key for the specified provider, with rotation and fallback logic."""
    if provider not in SidebarComponent.LLM_PROVIDERS:
        return None
        
    key_name = SidebarComponent.LLM_PROVIDERS[provider]["key_name"]
    keys = st.session_state.config.get('api_keys', {}).get(key_name, [])
    
    # Convert to list if not already
    if not isinstance(keys, list):
        keys = [keys] if keys else []
    
    if not keys:
        return None
        
    # Initialize key rotation index if not exists
    if 'key_rotation_index' not in st.session_state:
        st.session_state.key_rotation_index = {}
    if key_name not in st.session_state.key_rotation_index:
        st.session_state.key_rotation_index[key_name] = 0
        
    # Get next key using rotation
    current_index = st.session_state.key_rotation_index[key_name]
    key = keys[current_index]
    
    # Update rotation index for next time
    st.session_state.key_rotation_index[key_name] = (current_index + 1) % len(keys)
    
    return key

def initialize_session_state():
    """Initialize session state without making API calls."""
    if 'config' not in st.session_state:
        st.session_state.config = {}
    
    if 'api_keys' not in st.session_state.config:
        st.session_state.config['api_keys'] = {}
        
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
        
    # Don't initialize LLM clients until needed
    if 'llm_clients' not in st.session_state:
        st.session_state.llm_clients = {}

def get_llm_client(provider: str):
    """Lazy initialization of LLM clients."""
    if provider not in st.session_state.llm_clients:
        api_key = get_api_key(provider)
        if not api_key:
            return None
            
        try:
            if provider == "DeepSeek":
                st.session_state.llm_clients[provider] = create_deepseek_client(api_key)
            elif provider == "OpenAI":
                st.session_state.llm_clients[provider] = OpenAI(api_key=api_key)
            elif provider == "Anthropic":
                st.session_state.llm_clients[provider] = Anthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing {provider} client: {str(e)}")
            return None
            
    return st.session_state.llm_clients.get(provider)

def initialize_torch():
    """Initialize PyTorch with proper error handling."""
    try:
        import warnings
        # Filter out the specific PyTorch warning about class paths
        warnings.filterwarnings('ignore', message='.*Examining the path of torch.classes raised.*')
        
        import torch
        # Ensure CUDA is available if needed
        if torch.cuda.is_available():
            torch.cuda.init()
    except Exception as e:
        logger.warning(f"PyTorch initialization warning (non-critical): {str(e)}")
        # Continue anyway as this is not critical for basic functionality

def render_dashboard():
    """Render the main dashboard."""
    try:
        initialize_torch()
    except Exception as e:
        logger.warning(f"PyTorch initialization warning (non-critical): {str(e)}")
    
    # Get sidebar component and render it
    sidebar = SidebarComponent()
    repo_path = sidebar.render()

    # Initialize active tab if not set
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "LLM Chat"  # Default to chat tab

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