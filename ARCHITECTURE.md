# Repository Crawler Architecture

## Project Overview
A Python-based tool for analyzing local repositories, featuring a Streamlit web interface for interactive exploration and token analysis.

## Directory Structure

```
Repository_Crawler/
├── frontend/
│ ├── components/
│ │ ├── file_tree.py      # Interactive file tree visualization
│ │ └── file_viewer.py    # File content display with syntax highlighting
│ ├── home.py             # Main page UI
│ └── settings.py         # Settings and configuration UI
├── backend/
│ └── core/
│   ├── crawler.py        # Repository traversal and analysis
│   ├── file_handler.py   # File operations and metadata
│   └── tokenizer.py      # Token analysis and calculations
├── config/
│ └── config.yaml         # Application configuration
├── logs/                 # Application logs
│ └── *.log
├── prompts/             # Generated analysis output
├── tests/              # Test suite
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

## Core Components

### Frontend (Streamlit UI)
- **File Tree Component**: Interactive repository structure visualization
  - Expandable directory tree
  - File selection handling
  - Path management
- **File Viewer Component**: Content display and analysis
  - Syntax highlighting for 25+ languages
  - File metadata display
  - Error handling for various file types

### Backend
- **Repository Crawler**: Core analysis engine
  - Configurable file filtering
  - Directory traversal
  - Ignore pattern management
- **File Handler**: File system operations
  - Safe file reading
  - Metadata extraction
  - Cross-platform compatibility
- **Token Analyzer**: Content analysis
  - Token counting
  - Language detection
  - Cost estimation

### Configuration
- **Location**: `/config/config.yaml`
- **Features**:
  - Extensive ignore patterns for common files/directories
  - Language-specific settings
  - Configurable logging
  - Token analysis settings
  - Output management

### Logging System
- Timestamped log files
- Configurable log levels
- Detailed error tracking
- Performance monitoring

## Data Flow
1. User inputs repository path via Streamlit UI
2. Configuration loaded from `config.yaml`
3. Repository crawler analyzes directory structure
4. File tree component renders repository structure
5. User interacts with file tree
6. File viewer displays selected content
7. Token analyzer processes content
8. Results displayed in UI

## Error Handling
- File permission errors
- Invalid paths
- Binary file detection
- Configuration errors
- Token analysis failures
- UI state management

## Performance Considerations
- Lazy loading of file contents
- Efficient tree traversal
- Configurable ignore patterns
- Memory-efficient file handling
- Responsive UI updates