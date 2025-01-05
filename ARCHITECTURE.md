# Repository Crawler Architecture

## Project Overview
A Python-based tool for analyzing local repositories, featuring a Streamlit web interface for interactive exploration and token analysis.

## Current Status (Updated 2025-01-05)

### Active Issues
1. **Codebase Overview Generation**:
   - Error: "'files' attribute missing in repository traversal"
   - Root cause: Incomplete implementation of file traversal system
   - Impact: Unable to generate XML-formatted codebase overview

2. **UI Component Issues**:
   - File tree visualization inconsistencies
   - Directory nesting display problems
   - File selection state persistence
   - Label accessibility warnings

3. **XML Generation**:
   - Formatting inconsistencies in nested structures
   - CDATA section handling improvements needed
   - Directory hierarchy representation issues

### Recent Changes
1. **Error Handling Improvements**:
   - Enhanced file content reading safety checks
   - Better binary file detection
   - Improved error messaging and logging
   - Added validation for file accessibility

2. **XML Format Updates**:
   - Implemented proper directory nesting
   - Added file metadata attributes
   - Improved CDATA wrapping for file contents
   - Enhanced indentation consistency

3. **UI Enhancements**:
   - Removed redundant copy button
   - Improved token analysis display
   - Enhanced error message presentation
   - Added file type detection

## Directory Structure

```
Repository_Crawler/
├── frontend/
│ ├── components/
│ │ ├── file_tree.py      # Interactive file tree visualization
│ │ └── file_viewer.py    # File content display with syntax highlighting
│ ├── codebase_view.py    # Complete codebase analysis view
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
├── tests/              # Test suite (planned)
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

## Core Components

### Frontend (Streamlit UI)
- **File Tree Component**: Interactive repository structure visualization
  - State-based directory expansion
  - File selection handling
  - Path management
  - Known Limitations:
    - Component nesting restrictions
    - Label accessibility requirements
    - State persistence challenges
    - Layout consistency issues

- **File Viewer Component**: Content display and analysis
  - Syntax highlighting for 25+ languages
  - File metadata display
  - Error handling for various file types

### Backend
- **Repository Crawler**: Core analysis engine
  - Configurable file filtering
  - Directory traversal
  - Ignore pattern management
  - Current Issues:
    - Incomplete file traversal implementation
    - Missing 'files' attribute handling
    - Error propagation improvements needed

- **File Handler**: File system operations
  - Safe file reading
  - Metadata extraction
  - Cross-platform compatibility
  - Recent Improvements:
    - Enhanced error handling
    - Binary file detection
    - Empty file validation

- **Token Analyzer**: Content analysis
  - Token counting
  - Language detection
  - Cost estimation

### XML Generation System
- **Purpose**: Generate structured codebase representation
- **Features**:
  - Hierarchical directory structure
  - File metadata inclusion
  - Content wrapping in CDATA
  - Proper indentation
- **Current Issues**:
  - Nested directory handling
  - CDATA section formatting
  - Path representation consistency

### Configuration
- **Location**: `/config/config.yaml`
- **Features**:
  - Extensive ignore patterns
  - Language-specific settings
  - Configurable logging
  - Token analysis settings

### Logging System
- Timestamped log files
- Configurable log levels
- Detailed error tracking
- Performance monitoring

## Next Steps
1. Fix repository traversal system
2. Improve XML generation formatting
3. Enhance error handling in file tree component
4. Address label accessibility warnings
5. Implement proper state management
6. Add comprehensive testing

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