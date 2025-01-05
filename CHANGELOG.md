# Changelog

## [0.2.1] - 2025-01-05

### Changed
- Reorganized directory structure:
  - Moved UI components to `/frontend`
  - Moved core logic to `/backend/core`
  - Kept configuration in root `/config` directory
- Updated import paths to reflect new structure
- Enhanced logging system with timestamped files

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
### Fixed
- Configuration file path handling
- Import path resolution
- Directory structure documentation

## [0.2.0] - 2025-01-05

### Added
- Streamlit web interface for better user interaction
- Interactive file tree with expandable directories
- Real-time file content viewer with syntax highlighting
- Dynamic configuration management through UI
- Support for 25+ programming languages
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