import os
import sqlite3
from typing import Optional
from datetime import datetime
from pathlib import Path

import streamlit as st
from backend.core.singleton_manager import get_manager

class SQLiteDB:
    """SQLite database manager that maintains a single connection instance."""
    
    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False
        self._db_path = Path(__file__).parent.parent.parent / 'data' / 'repo_crawler.db'

    def initialize(self) -> None:
        """Initialize the SQLite database connection and create tables."""
        if not self._initialized:
            # Ensure data directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection with row factory for dict-like access
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            
            # Create tables
            with self._conn:
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT NOT NULL UNIQUE,
                        last_scan TEXT,
                        total_files INTEGER,
                        total_size INTEGER,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repo_id INTEGER NOT NULL,
                        path TEXT NOT NULL,
                        size INTEGER NOT NULL,
                        content TEXT,
                        token_count INTEGER,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (repo_id) REFERENCES repositories(id),
                        UNIQUE(repo_id, path)
                    )
                """)
            
            self._initialized = True

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        """Get the database connection."""
        return self._conn

    def insert_message(self, message: str) -> None:
        """Insert a message into the messages table."""
        if not self._initialized or not self._conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        with self._conn:
            self._conn.execute(
                "INSERT INTO messages (message, created_at) VALUES (?, ?)",
                (message, datetime.now().isoformat())
            )

    def insert_repository(self, path: str, total_files: int, total_size: int) -> int:
        """Insert or update repository information."""
        if not self._initialized or not self._conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        now = datetime.now().isoformat()
        with self._conn:
            cursor = self._conn.execute("""
                INSERT INTO repositories (path, last_scan, total_files, total_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    last_scan=excluded.last_scan,
                    total_files=excluded.total_files,
                    total_size=excluded.total_size,
                    updated_at=excluded.updated_at
                RETURNING id
            """, (path, now, total_files, total_size, now, now))
            return cursor.fetchone()[0]

    def insert_file(self, repo_id: int, path: str, size: int, content: Optional[str] = None, token_count: Optional[int] = None) -> None:
        """Insert or update file information."""
        if not self._initialized or not self._conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        now = datetime.now().isoformat()
        with self._conn:
            self._conn.execute("""
                INSERT INTO files (repo_id, path, size, content, token_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_id, path) DO UPDATE SET
                    size=excluded.size,
                    content=excluded.content,
                    token_count=excluded.token_count,
                    updated_at=excluded.updated_at
            """, (repo_id, path, size, content, token_count, now, now))

def get_db() -> SQLiteDB:
    """Get or create the SQLite singleton instance."""
    manager = get_manager()
    db = manager.get('sqlite')
    
    if not db:
        db = SQLiteDB()
        manager.register('sqlite', db)
        db.initialize()
    
    return db 