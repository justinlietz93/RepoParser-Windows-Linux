# NOTE: This project is still in progress and unfinished

# Repository Crawler 🔍

A powerful Python-based tool that quickly produces context prompts for LLMs by analyzing local repositories and generating structured documentation with token cost estimation. Built with Streamlit, it provides an intuitive web interface for exploring codebases and understanding their token usage in the context of AI language models.

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
   pip install -r requirements.txt
   ```

### Running the App

1. Start the Streamlit application:
   ```bash
   streamlit run main.py
   ```

2. The web interface will open in your default browser

### Using the Interface

1. **Repository Configuration**:
   - Enter your repository path in the sidebar
   - Add/remove file extensions to analyze
   - Manage ignore patterns for files and directories

2. **File Navigation**:
   - Browse the interactive file tree in the left panel
   - Click on files to view their contents
   - Directories expand/collapse on click

3. **File Analysis**:
   - View syntax-highlighted file contents
   - See file metadata and statistics
   - Get token analysis and cost estimates

## Configuration

The application maintains configuration in `config/config.yaml`, but you can manage all settings through the UI:

- File extensions to include
- Directories and files to ignore
- Output preferences
- Logging settings

## Supported Languages

The file viewer supports syntax highlighting for:
- Python (.py)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- HTML (.html)
- CSS (.css)
- JSON (.json)
- YAML (.yaml, .yml)
- Markdown (.md)
- Shell scripts (.sh, .bash)
- SQL (.sql)
- C/C++ (.c, .cpp, .h)
- Java (.java)
- Go (.go)
- Rust (.rs)
- PHP (.php)
- Ruby (.rb)
- Swift (.swift)
- Kotlin (.kt)
- R (.r)
- XML (.xml)
- Dockerfiles
