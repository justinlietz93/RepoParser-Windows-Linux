# NOTE: This project is still in progress and unfinished
# You can grab the dev branch for features in development, but there are currently many bugs as I am using an experimental AI only development technique. This entire program was written by AI ONLY

# Repository Crawler 🔍

A powerful Python-based tool that analyzes local repositories and generates structured documentation with token cost estimation. Built with Streamlit, it provides an intuitive web interface for exploring codebases and understanding their token usage in the context of AI language models.

## Features

- 📁 File tree visualization
- 📝 Syntax-highlighted code viewer
- 🔢 Token analysis and cost estimation for AI models
- ⚙️ Configurable file extensions and ignore patterns
- 📊 Detailed logging and error handling
- 💾 Customizable output formats

## Quick Start

### Prerequisites

- Python 3.6+
- Git (for cloning the repository)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/justinlietz93/RepoParser.git
   cd RepoParser
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   # First, upgrade pip
   python -m pip install --upgrade pip

   # Install core dependencies
   pip install pyyaml streamlit tiktoken pathlib

   # Or install all dependencies from requirements.txt
   pip install -r requirements.txt
   ```

   If you encounter any errors, try installing dependencies individually:
   ```bash
   pip install pyyaml
   pip install streamlit
   pip install tiktoken
   pip install pathlib
   ```

4. Verify installation:
   ```bash
   python -c "import yaml; import streamlit; import tiktoken; print('All dependencies installed successfully!')"
   ```

### Running the App

1. Start the application:
   ```bash
   python main.py
   ```

2. The script will prompt you for:
   - Repository path to analyze
   - Model selection for token analysis
   - Output preferences

3. Results will be saved in the `prompts` directory

### Basic Usage

1. **Repository Analysis**:
   - Provide the full path to your local repository
   - Select an AI model for token analysis
   - The script will analyze the repository structure

2. **View Results**:
   - Check the generated file tree
   - Review file contents with syntax highlighting
   - See token analysis and cost estimates

3. **Configure Settings**:
   - Edit config/config.yaml for customization
   - Adjust file extensions to include/exclude
   - Modify ignore patterns for files/directories
   - Set logging preferences

## Configuration

The application can be configured by editing `config/config.yaml`:

```yaml
# Example configuration
# Directory settings
local_root: "C:\\Github\\path\\to\\your\\project"
output_directory: "prompts"
output_filename: "example_generated_prompt.txt"

# File extensions to include
included_extensions:
  - ".py"
  - ".ipynb"
  - ".html"
  - ".css"
  - ".js"
  - ".jsx"
  - ".md"
  - ".rst"

# Ignore patterns
ignore_patterns:
  directories:
    - ".git"
    - ".github"
    - "__pycache__"
    - "node_modules"
    - "venv"
    - ".venv"
    - "env"
    - ".env"
    - "build"
    - "dist"
    - ".idea"
    - ".vscode"
    - "vendor"
    - "site-packages"
    - "tests"  # Custom ignore
    - "docs"   # Custom ignore
  files:
    - "*.pyc"
    - "*.pyo"
    - "*.pyd"
    - "*.so"
    - "*.dll"
    - "*.dylib"
    - "*.egg-info"
    - "*.egg"
    - "*.whl"
    - ".DS_Store"
    - "Thumbs.db"
    - "*.log"
    - ".env"
    - ".gitignore"
    - "*.lock"
    - "package-lock.json"
    - "*.md"      # Custom ignore
    - "*.test.js" # Custom ignore

# Logging configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(levelname)s - %(message)s"
  datefmt: "%Y-%m-%d %H:%M:%S"

```
