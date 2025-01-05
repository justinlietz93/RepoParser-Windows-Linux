# Repository Crawler Architecture

## Project Overview
A Python-based tool that crawls local repositories and generates structured documentation, featuring a modern Streamlit web interface for interactive repository exploration and token analysis.

## Core Components

### Crawler Module (`core/crawler.py`)
- Handles repository traversal
- Implements file filtering
- Manages directory tree generation
- Processes file contents
- Returns structured file tree data

### File Handler Module (`core/file_handler.py`)
- Manages file operations
- Handles file reading/writing
- Implements error handling
- Ensures cross-platform compatibility
- Provides file metadata

### Tokenizer Module (`core/tokenizer.py`)
- Analyzes file contents for token usage
- Calculates token costs for AI models
- Provides token statistics and metrics
- Handles different tokenization models
- Real-time token analysis

## User Interface

### Streamlit Application (`main.py`)
- Main entry point for web interface
- Handles routing between components
- Manages global state and session data
- Implements responsive layout
- Coordinates component interactions
- Handles configuration persistence

### Components
1. File Tree (`app/components/file_tree.py`)
   - Interactive tree visualization
   - Directory expansion/collapse
   - File selection handling
   - Tree state management
   - Path generation and validation

2. File Viewer (`app/components/file_viewer.py`)
   - Content display with syntax highlighting
   - Language detection
   - File information display
   - Error handling for binary files
   - Metadata visualization

## Configuration Management

### Config Module (`config/config.yaml`)
- File extension settings
- Ignore patterns
- Output settings
- Logging configuration
- UI preferences

### Memory Management (`memory.json`)
- Project metadata storage
- Feature tracking
- Dependency management
- Configuration state
- Session persistence

## Directory Structure 
repo_crawler/
├── app/
│ ├── components/
│ │ ├── file_tree.py
│ │ └── file_viewer.py
├── core/
│ ├── crawler.py
│ ├── file_handler.py
│ └── tokenizer.py
├── config/
│ └── config.yaml
├── prompts/
│ └── .gitkeep
├── main.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── memory.json
└── ARCHITECTURE.md

## Data Flow

1. User Input
   - Repository path selection
   - Configuration updates
   - File selection events
   - UI interactions

2. Core Processing
   - Directory traversal
   - File filtering
   - Content extraction
   - Token analysis
   - Tree generation
   - Language detection

3. State Management
   - Session state updates
   - Configuration persistence
   - File selection tracking
   - Tree state maintenance

4. Output Generation
   - Interactive file tree
   - Syntax-highlighted content
   - Token statistics
   - File metadata
   - Error messages

## Error Handling
- File permission errors
- Invalid paths
- Decoding issues
- Configuration errors
- Token processing errors
- Binary file detection
- UI state conflicts

## Performance Considerations
- Lazy loading of file contents
- Efficient tree traversal
- Caching of token analysis
- Optimized UI updates
- Responsive file handling