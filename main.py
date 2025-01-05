import os
import logging
import fnmatch

# Add default ignore patterns at the top of the file
DEFAULT_IGNORE_PATTERNS = {
    'directories': {
        '.git',
        '.github',
        '__pycache__',
        'node_modules',
        'venv',
        '.venv',
        'env',
        '.env',
        'build',
        'dist',
        '.idea',
        '.vscode',
        'vendor',
        'site-packages',
    },
    'files': {
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '*.so',
        '*.dll',
        '*.dylib',
        '*.egg-info',
        '*.egg',
        '*.whl',
        '.DS_Store',
        'Thumbs.db',
        '*.log',
        '.env',
        '.gitignore',
        '*.lock',
        'package-lock.json',
    }
}

# Add logging configuration at the top of the file
def setup_logging():
    """Configure logging with a specific format"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def build_local_directory_tree(
    root_path, 
    indent=0, 
    included_extensions=None, 
    ignore_patterns=None
):
    """
    Recursively builds a string representation of the directory structure 
    and returns a list of file paths (with indentation levels) for files 
    that match the included_extensions.
    
    Args:
        root_path: The starting directory path
        indent: Current indentation level
        included_extensions: Tuple of file extensions to include
        ignore_patterns: Dict with 'directories' and 'files' sets of patterns to ignore
    """
    logger = logging.getLogger(__name__)
    
    if included_extensions is None:
        included_extensions = ('.py', '.ipynb', '.html', '.css', '.js', '.jsx', '.md', '.rst')
    
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    logger.info(f"Scanning directory: {root_path}")
    tree_str = ""
    file_paths = []

    try:
        items = sorted(os.listdir(root_path))
    except PermissionError:
        logger.warning(f"Permission denied accessing directory: {root_path}")
        return tree_str, file_paths

    for item in items:
        item_full_path = os.path.join(root_path, item)
        
        # Check if directory should be ignored
        if os.path.isdir(item_full_path):
            if any(fnmatch.fnmatch(item, pattern) for pattern in ignore_patterns['directories']):
                logger.debug(f"Ignoring directory (matched ignore pattern): {item_full_path}")
                continue
            
            logger.debug(f"Found directory: {item_full_path}")
            tree_str += '    ' * indent + f"[{item}/]\n"
            sub_tree_str, sub_file_paths = build_local_directory_tree(
                item_full_path,
                indent + 1,
                included_extensions,
                ignore_patterns
            )
            tree_str += sub_tree_str
            file_paths.extend(sub_file_paths)
        else:
            # Check if file should be ignored
            if any(fnmatch.fnmatch(item, pattern) for pattern in ignore_patterns['files']):
                logger.debug(f"Ignoring file (matched ignore pattern): {item_full_path}")
                continue
                
            tree_str += '    ' * indent + f"{item}\n"
            if item.lower().endswith(included_extensions):
                logger.info(f"Processing file: {item_full_path}")
                file_paths.append((indent, item_full_path))
            else:
                logger.debug(f"Skipping file with non-matching extension: {item_full_path}")
    
    return tree_str, file_paths


def read_file_contents(file_path):
    """
    Safely reads a text file and returns its contents as a string.
    """
    logger = logging.getLogger(__name__)
    try:
        logger.debug(f"Reading contents of file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        logger.error(f"Failed to decode file: {file_path}")
        return "Unable to decode file contents."
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"


def create_local_repo_prompt(
    root_path, 
    included_extensions=None, 
    ignore_patterns=None
):
    """
    Builds a directory structure string and then appends each file's contents.
    
    Args:
        root_path: The starting directory path
        included_extensions: Tuple of file extensions to include
        ignore_patterns: Dict with 'directories' and 'files' sets of patterns to ignore
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting to process repository at: {root_path}")
    
    directory_tree, file_paths = build_local_directory_tree(
        root_path, 
        included_extensions=included_extensions,
        ignore_patterns=ignore_patterns
    )

    # Start assembling the output
    output_str = f"Directory Structure:\n{directory_tree}\n"

    # Append file contents
    for indent, path in file_paths:
        logger.info(f"Adding contents of file to output: {path}")
        file_content = read_file_contents(path)
        rel_path = os.path.relpath(path, root_path)  # relative path for neatness
        output_str += '\n' + '    ' * indent + f"{rel_path}:\n"
        output_str += '    ' * indent + '```\n'
        output_str += file_content
        output_str += '\n' + '    ' * indent + '```\n'
    
    return output_str


if __name__ == "__main__":
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Example usage with custom ignore patterns
    local_root = "C:\\Github\\ticket_tracker\\ticket_tracker"
    output_file_name = "ticket_tracker_prompt.txt"
    
    # Example of adding custom ignore patterns
    custom_ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()
    custom_ignore_patterns['directories'].update({
        'tests',  # Ignore test directories
        'docs',   # Ignore documentation
    })
    custom_ignore_patterns['files'].update({
        '*.md',   # Ignore markdown files
        '*.test.js',  # Ignore test files
    })

    logger.info(f"Starting script with root directory: {local_root}")
    result_string = create_local_repo_prompt(
        local_root,
        ignore_patterns=custom_ignore_patterns
    )
    
    logger.info(f"Writing results to file: {output_file_name}")
    with open(output_file_name, 'w', encoding='utf-8') as file:
        file.write(result_string)

    logger.info(f"Local codebase information has been saved to {output_file_name}")
