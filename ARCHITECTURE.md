# Repository Crawler Architecture

## Project Overview
A Python-based tool that crawls local repositories and generates structured documentation, with both CLI and Streamlit web interface options.

## Core Components

### Crawler Module (`core/crawler.py`)
- Handles repository traversal
- Implements file filtering
- Manages directory tree generation
- Processes file contents

### File Handler Module (`core/file_handler.py`)
- Manages file operations
- Handles file reading/writing
- Implements error handling
- Ensures cross-platform compatibility

## User Interface

### Streamlit Application (`streamlit_app.py`)
- Main entry point for web interface
- Handles routing between pages
- Manages global state
- Implements responsive layout

### Pages
1. Home Page (`app/pages/home.py`)
   - Repository path input
   - Analysis triggering
   - Results display

2. Settings Page (`app/pages/settings.py`)
   - Configuration management
   - Extension settings
   - Ignore pattern management

### Components
1. File Tree (`app/components/file_tree.py`)
   - Tree visualization
   - Directory structure display
   - Interactive navigation

2. File Viewer (`app/components/file_viewer.py`)
   - Content display
   - Syntax highlighting
   - File information

## Configuration Management

### Config Module (`config/config.yaml`)
- File extension settings
- Ignore patterns
- Output settings
- Logging configuration

## Directory Structure 
repo_crawler/
├── app/
│ ├── init.py
│ ├── pages/
│ │ ├── init.py
│ │ ├── home.py
│ │ └── settings.py
│ ├── components/
│ │ ├── init.py
│ │ ├── file_tree.py
│ │ └── file_viewer.py
│ └── utils/
│ ├── init.py
│ └── styling.py
├── core/
│ ├── init.py
│ ├── crawler.py
│ └── file_handler.py
├── config/
│ ├── init.py
│ └── config.yaml
├── prompts/
│ └── .gitkeep
├── tests/
│ ├── init.py
│ ├── test_crawler.py
│ └── test_file_handler.py
├── main.py
├── streamlit_app.py
├── requirements.txt
├── README.md
└── ARCHITECTURE.md

## Data Flow

1. User Input
   - Repository path selection
   - Configuration settings
   - Analysis triggers

2. Core Processing
   - Directory traversal
   - File filtering
   - Content extraction
   - Tree generation

3. Output Generation
   - File tree visualization
   - Content display
   - Configuration storage

## Error Handling
- File permission errors
- Invalid paths
- Decoding issues
- Configuration errors