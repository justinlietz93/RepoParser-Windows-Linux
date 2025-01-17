# Repository Crawler Architecture

## System Overview

The Repository Crawler is a Python-based application that analyzes local repositories to generate context prompts for LLMs. It follows a clean architecture pattern with clear separation of concerns.

## Core Components

### 1. Frontend Layer (`/frontend`)
- **Streamlit-based UI**
  - `home.py`: Main application interface
  - `settings.py`: Configuration management
  - `components/`: Reusable UI components
    - `sidebar.py`: Navigation and controls
    - `file_tree.py`: Repository visualization
    - `ignore_tree.py`: Pattern management

### 2. Backend Layer (`/backend`)
- **Core Logic**
  - `core/crawler.py`: Repository traversal engine
  - `core/singleton_manager.py`: State management
  - `database/db_manager.py`: Data persistence

### 3. Configuration (`/config`)
- YAML-based configuration system
- Environment-specific settings
- Ignore patterns management

### 4. Logging System (`/logs`)
- Daily rotating log files
- Structured logging format
- Debug and production modes

## Design Patterns

1. **Singleton Pattern**
   - Used in `singleton_manager.py`
   - Ensures single instance of critical components

2. **Strategy Pattern**
   - Implemented in crawler for different traversal strategies
   - Allows flexible ignore pattern matching

3. **Observer Pattern**
   - Used for UI updates and state management
   - Streamlit session state integration

## Data Flow

1. User selects repository via UI
2. Frontend validates input
3. Backend crawler traverses repository
4. Results cached for performance
5. UI updates with analysis

## Performance Optimizations

1. File Tree Caching
   - Hash-based cache invalidation
   - Memory-efficient tree structure

2. Lazy Loading
   - On-demand file content reading
   - Partial tree expansion

## Security Considerations

1. Path Traversal Protection
2. Configuration Validation
3. Error Handling and Logging
4. Input Sanitization

## Testing Strategy

1. Unit Tests
   - `tests/test_crawler.py`: Core functionality
   - Pattern matching validation
   - Cache behavior verification

2. Integration Tests
   - UI component interaction
   - End-to-end workflows

## Future Enhancements

1. Improved Repository Traversal
   - Parallel processing
   - Incremental updates

2. Enhanced Token Analysis
   - Multiple model support
   - Cost optimization

3. Cross-Platform Compatibility
   - Path handling improvements
   - OS-specific optimizations

## Dependencies

Core:
- streamlit>=1.22.0
- pyyaml>=6.0.0
- tiktoken>=0.5.1
- pathlib>=1.0.1

Development:
- pytest>=7.0.0
- black>=22.0.0
- flake8>=6.0.0
- mypy>=1.0.0

## Configuration Schema

```yaml
ignore_patterns:
  directories:
    - .git
    - __pycache__
    # ... more patterns
  files:
    - "*.pyc"
    - "*.log"
    # ... more patterns
```

## Error Handling

1. Graceful Degradation
2. User-Friendly Error Messages
3. Detailed Logging
4. Recovery Mechanisms

## Deployment Considerations

1. Environment Setup
2. Dependency Management
3. Logging Configuration
4. Performance Monitoring 