from typing import Optional
import logging
from pathlib import Path

class FileHandler:
    """Handles file operations with proper error handling."""
    
    def __init__(self):
        """Initialize the file handler."""
        self.logger = logging.getLogger(__name__)
        
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Safely read file contents.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File contents as string or None if error occurs
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            self.logger.error(f"Failed to decode file: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
            
    def write_file(self, file_path: str, content: str) -> bool:
        """
        Safely write content to file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {str(e)}")
            return False 