# Repository Crawler 🔍

> ⚠️ **IMPORTANT: Work in Progress** ⚠️
> 
> This project is under active development and is **NOT** production-ready. Use at your own discretion.
> Features may be incomplete, unstable, or change without notice.

## Overview

Repository Crawler is an experimental tool that combines multi-agent LLM analysis with local codebase exploration. It provides a streamlined interface for code analysis, documentation, and understanding through:

- 🌲 Interactive file tree visualization
- 🤖 Multi-agent LLM analysis (up to 25 specialized roles)
- 💾 Persistent memory using ChromaDB
- 📊 Real-time token usage and cost tracking
- 🔄 Parallel agent analysis capabilities
- 🔑 Flexible API key management

## Current Status

- **Alpha Stage**: Core functionality is implemented but undergoing frequent changes
- **Performance**: Large repositories may experience slowdowns
- **Stability**: Expect occasional errors and edge cases
- **Security**: Basic validation implemented, but needs further hardening

## Supported LLM Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- DeepSeek
- Google (Gemini 1.5 Pro) - Coordinator for multi-agent synthesis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/repo_crawler.git
cd repo_crawler

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Configure your environment:
   - Add API keys in the LLM Settings tab
   - Set up repository path in File Settings
   - Configure ignore patterns if needed

## Known Limitations

- Large repositories (>1GB or >10k files) may experience performance issues
- Memory usage can be significant with large codebases
- Some features are experimental and may not work as expected
- UI responsiveness varies with repository size

## Contributing

This project is in active development. While contributions are welcome, please note that significant changes may occur.

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## License

[Your License Here]

## Disclaimer

⚠️ This software is provided "as is", without warranty of any kind. Use at your own risk. The authors assume no liability for data loss, system damage, or any other issues that may arise from using this software.