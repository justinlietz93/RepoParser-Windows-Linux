# Repository Crawler 🔍

> **⚠️ Project Status: Active Development**  
> This project is under active development. While core functionality is operational, you may encounter bugs or incomplete features. See [Missing Features](#missing-features) section for planned improvements.

A powerful Python-based tool that quickly produces context prompts for LLMs by analyzing local repositories and generating structured documentation with token cost estimation. Built with Streamlit, it provides an intuitive web interface for exploring codebases and understanding their token usage in the context of AI language models.

## ⚡ Quickstart

```bash
# Clone repository
git clone https://github.com/justinlietz93/RepoPrompt-Windows-Linux.git
cd repo_crawler

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start application
streamlit run main.py

A powerful Python-based tool that quickly produces context prompts for LLMs by analyzing local repositories and generating structured documentation with token cost estimation. Built with Streamlit, it provides an intuitive web interface for exploring codebases and understanding their token usage in the context of AI language models.

## Features

### 🎯 Core Features
- Interactive repository exploration
- Token analysis with GPT model support
- Cross-platform compatibility
- Configurable ignore patterns
- XML-formatted codebase overview

### 🎨 Modern UI
- Tabbed sidebar interface for better organization
  - Settings: Model and repository configuration
  - Files: Upload and manage system files
  - Patterns: Configure ignore patterns
- Visual file browser for repository selection
- Interactive file tree visualization
- Syntax highlighting for 25+ languages
- Token analysis visualization

### 🔧 Configuration
- Extensive ignore patterns for files and directories
- Multiple GPT model support
  - GPT-4 (default)
  - GPT-4-32k
  - GPT-3.5-turbo
  - GPT-3.5-turbo-16k
- Cross-platform path handling
- Configurable logging system

## Detailed Installation

1. Clone the repository:
```bash
git clone https://github.com/justinlietz93/RepoPrompt-Windows-Linux.git
cd repo_crawler
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage Guide

1. Start the application:
```bash
streamlit run main.py
```

2. Using the interface:
   - Select repository using the visual file browser
   - Choose token analysis model
   - Configure ignore patterns if needed
   - Upload system files (config, rules, etc.)
   - Click "Generate Prompt" to analyze

## Configuration

### Repository Settings
- Use the Settings tab to:
  - Select token analysis model
  - Set repository path via browser or manual input

### File Management
- Use the Files tab to:
  - Upload configuration files (.yaml, .yml)
  - Upload rule files (.txt, .md, .cursorrules)
  - View and manage loaded files

### Pattern Management
- Use the Patterns tab to:
  - Configure ignored directories
  - Set ignored file patterns
  - Download current configuration

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

### Project Structure
```
Repository_Crawler/
├── frontend/          # UI components
├── backend/           # Core functionality
├── config/           # Configuration files
├── logs/            # Application logs
├── prompts/         # Generated output
└── tests/          # Test suite
```

## Known Issues
- Repository traversal system needs improvement
- XML generation formatting issues
- UI component state persistence
- Linux / Mac compatibility verification needed

## Missing Features

### Planned Core Features
1. **Advanced Repository Analysis**
   - [ ] Dependency graph generation
   - [ ] Code complexity metrics
   - [ ] Custom pattern definition UI
   - [ ] Batch repository processing

2. **Enhanced Token Analysis**
   - [ ] Custom model support
   - [ ] Token cost optimization suggestions
   - [ ] Batch processing capabilities
   - [ ] Token usage analytics

3. **UI Improvements**
   - [ ] Dark mode support
   - [ ] Customizable themes
   - [ ] Advanced file filtering
   - [ ] Search functionality
   - [ ] Real-time updates

4. **Export Capabilities**
   - [ ] Multiple export formats (JSON, YAML, XML)
   - [ ] Custom template support
   - [ ] Batch export functionality
   - [ ] Report generation

5. **Integration Features**
   - [ ] Git integration
   - [ ] CI/CD pipeline support
   - [ ] API endpoint
   - [ ] Plugin system

### Development Roadmap
1. Repository traversal system enhancement
2. XML generation improvements
3. Error handling expansion
4. Comprehensive testing implementation
5. Cross-platform compatibility verification

## License
[MIT License](LICENSE)

## Support
For support, please open an issue in the GitHub repository.

---
> **Note**: This project is under active development. Features may be added, modified, or removed. Please check the repository regularly for updates.