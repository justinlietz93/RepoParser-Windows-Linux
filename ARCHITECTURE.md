# Repository Crawler Architecture

## Project Overview
A Python-based tool for analyzing local repositories, featuring a Streamlit web interface for interactive exploration and token analysis. Designed to be cross-platform compatible (Windows, Linux, macOS).

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
1. **Sidebar Reorganization**:
   - Implemented tabbed interface (Settings, Files, Patterns)
   - Added visual file browser for repository selection
   - Improved model selection UI
   - Enhanced file upload system
   - Streamlined pattern management

2. **Model Configuration Updates**:
   - Changed default model to GPT-4
   - Improved model selection UI
   - Added model persistence
   - Fixed token analyzer configuration

3. **Logging System Improvements**:
   - Consolidated logging configuration
   - Single log file per run
   - Improved log message format
   - Better error tracking

4. **XML Format Updates**:
   - Implemented proper directory nesting
   - Added full path support in tags
   - Improved CDATA wrapping
   - Enhanced indentation consistency

5. **UI Enhancements**:
   - Removed redundant copy button
   - Improved token analysis display
   - Enhanced error message presentation
   - Added file type detection

## Directory Structure

```
Repository_Crawler/
├── frontend/
│ ├── components/
│ │ ├── sidebar.py       # Tabbed sidebar interface
│ │ ├── file_tree.py     # Interactive file tree visualization
│ │ └── file_viewer.py   # File content display with syntax highlighting
│ ├── codebase_view.py   # Complete codebase analysis view
│ ├── home.py            # Main page UI
│ └── settings.py        # Settings and configuration UI
├── backend/
│ └── core/
│   ├── crawler.py       # Repository traversal and analysis
│   ├── file_handler.py  # File operations and metadata
│   └── tokenizer.py     # Token analysis and calculations
├── config/
│ └── config.yaml        # Application configuration
├── logs/                # Application logs
│ └── *.log
├── prompts/            # Generated analysis output
├── tests/             # Test suite (planned)
├── main.py            # Application entry point
└── requirements.txt   # Python dependencies
```

## Core Components

### Frontend (Streamlit UI)
- **Sidebar Component**: Main navigation and configuration interface
  - Tabbed interface for better organization
  - Settings tab: Model selection and repository configuration
  - Files tab: File upload and management
  - Patterns tab: Ignore pattern configuration
  - Visual file browser for repository selection
  - Known Limitations:
    - State persistence between tabs
    - Layout consistency in different screen sizes

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
  - Platform-agnostic path handling
  - Current Issues:
    - Incomplete file traversal implementation
    - Missing 'files' attribute handling
    - Error propagation improvements needed
    - Linux permission handling verification needed

- **File Handler**: File system operations
  - Safe file reading
  - Metadata extraction
  - Cross-platform compatibility
    - pathlib.Path for path operations
    - UTF-8 file encoding
    - Platform-agnostic file access
  - Recent Improvements:
    - Enhanced error handling
    - Binary file detection
    - Empty file validation
    - Standardized path handling

- **Token Analyzer**: Content analysis
  - Token counting (GPT-4 default)
  - Language detection
  - Cost estimation
  - Model persistence

### XML Generation System
- **Purpose**: Generate structured codebase representation
- **Features**:
  - Hierarchical directory structure
  - Full path support in tags
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
  - Model configuration (GPT-4 default)
  - Configurable logging
  - Platform-specific settings (planned)

### Cross-Platform Compatibility
- **Path Handling**:
  - Using pathlib.Path throughout
  - Platform-agnostic path separators
  - Case-sensitive path handling
  
- **File Operations**:
  - UTF-8 encoding by default
  - Platform-specific file permissions
  - Binary file detection
  
- **Known Issues**:
  - Linux file permission verification needed
  - Case sensitivity handling in file paths
  - Path separator consistency in XML output

### Logging System
- Single log file per run
- Simplified log format
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