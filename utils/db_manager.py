import sqlite3
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "./data/local.db"):
        """Initialize database manager with local storage path."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()
    
    def _initialize_db(self):
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    provider TEXT PRIMARY KEY,
                    keys TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_api_keys(self, provider: str, keys: list[str]):
        """Save API keys for a provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Store keys as JSON string
                keys_json = json.dumps(keys)
                cursor.execute("""
                    INSERT OR REPLACE INTO api_keys (provider, keys)
                    VALUES (?, ?)
                """, (provider, keys_json))
                conn.commit()
                logger.info(f"Saved API keys for {provider}")
                return True
        except Exception as e:
            logger.error(f"Error saving API keys: {str(e)}")
            return False
    
    def get_api_keys(self, provider: str = None) -> dict:
        """Get API keys for a provider or all providers."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if provider:
                    cursor.execute("SELECT provider, keys FROM api_keys WHERE provider = ?", (provider,))
                    row = cursor.fetchone()
                    if row:
                        return {row[0]: json.loads(row[1])}
                    return {}
                else:
                    cursor.execute("SELECT provider, keys FROM api_keys")
                    return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error retrieving API keys: {str(e)}")
            return {}
    
    def delete_api_keys(self, provider: str) -> bool:
        """Delete API keys for a provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM api_keys WHERE provider = ?", (provider,))
                conn.commit()
                logger.info(f"Deleted API keys for {provider}")
                return True
        except Exception as e:
            logger.error(f"Error deleting API keys: {str(e)}")
            return False 