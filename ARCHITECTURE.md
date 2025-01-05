# Repository Crawler Architecture

## Directory Structure

```
Repository_Crawler/
├── frontend/
│ ├── components/
│ │ ├── file_tree.py
│ │ └── file_viewer.py
│ ├── home.py
│ └── settings.py
├── backend/
│ └── core/
│   ├── crawler.py
│   ├── file_handler.py
│   └── tokenizer.py
├── config/
│ └── config.yaml
├── logs/
│ └── *.log
├── prompts/
├── tests/
├── main.py
├── ARCHITECTURE.md
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## Core Components

### Configuration
- Located in `/config/config.yaml`
- Stores application settings and ignore patterns
- Managed through the UI settings panel

### Frontend
- Components for file tree visualization and content viewing
- Settings management and configuration interface
- Located in `/frontend` directory

### Backend
- Core logic for repository analysis and token calculation
- File system operations and crawling functionality
- Located in `/backend/core` directory

### Logging
- Detailed application logs stored in `/logs`
- Timestamped log files for debugging and monitoring

## Data Flow
1. User inputs repository path through UI
2. Configuration loaded from `/config/config.yaml`
3. Repository crawler analyzes directory structure
4. File tree component displays repository structure
5. User selects files for viewing
6. File viewer displays content with syntax highlighting
7. Token analyzer processes file content
8. Results displayed in UI

## Key Classes

### RepositoryCrawler
- Handles repository traversal
- Manages file filtering based on ignore patterns
- Builds directory tree structure

### FileViewer
- Displays file contents
- Provides syntax highlighting
- Shows file metadata

### TokenAnalyzer
- Analyzes file content
- Calculates token statistics
- Supports multiple programming languages

### FileTreeComponent
- Renders interactive file tree
- Handles file selection
- Manages tree state

## Configuration Management
- UI-based configuration editing
- Automatic config file updates
- Default patterns for common ignore cases