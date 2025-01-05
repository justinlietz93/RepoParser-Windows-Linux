# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-01-05

### Added
- New Codebase Overview page with:
  - Complete codebase JSON view
  - Total token count display
  - Cost estimation for different models
  - Model selection for cost calculation
- Collapsible hierarchical file tree with:
  - Directory expansion/collapse controls
  - Proper indentation for nested files
  - Sorted directories and files
  - Improved visual indicators

### Enhanced
- Improved navigation with tabbed interface
- Made Codebase Overview the default view
- Token analysis visualization
- Cost calculation accuracy
- Separated UI logic into dedicated dashboard module

### Changed
- Moved UI code from main.py to frontend/dashboard.py
- Simplified main.py to handle only app initialization
- Improved code organization and maintainability
- Redesigned file tree component for better UX

### Fixed
- File tree initialization error
- Repository root path handling
- Directory structure traversal

## [0.2.2] - 2025-01-05

### Added
- Comprehensive default ignore patterns in config.yaml
- Support for 25+ programming languages
- Detailed logging with timestamps
- Binary file detection and handling

### Enhanced
- Configuration file with extensive default settings
- File extension support for multiple languages
- Error handling and logging system
- Documentation clarity and completeness

### Fixed
- Configuration file path handling
- Import path resolution
- Directory structure documentation

## [0.2.1] - 2025-01-05

### Changed
- Reorganized directory structure:
  - Moved UI components to `/frontend`
  - Moved core logic to `/backend/core`
  - Kept configuration in root `/config` directory
- Updated import paths to reflect new structure
- Enhanced logging system with timestamped files

## [0.2.0] - 2025-01-05

### Added
- Streamlit web interface for better user interaction
- Interactive file tree with expandable directories
- Real-time file content viewer with syntax highlighting
- Dynamic configuration management through UI
- File metadata and statistics display
- Token analysis visualization
- Session state management
- Persistent configuration storage

### Changed
- Migrated from CLI to web-based interface
- Improved file tree visualization
- Enhanced configuration management
- Updated documentation to reflect new UI
- Restructured project architecture

### Removed
- Command-line interface
- Static configuration file editing
- Manual file tree generation
- Direct file system output

## [0.1.0] - 2025-01-05

### Added
- Initial release
- Basic repository crawling functionality
- File tree generation
- Token analysis
- Configuration file support
- Basic logging
- Command-line interface 