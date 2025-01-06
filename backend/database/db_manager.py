# Repo_Crawler/backend/database/db_manager.py

import os
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
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
        """Initialize the SQLite database connection, create tables, and indexes."""
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

            # Create indexes for faster lookups
            self._create_indexes()

            self._initialized = True

    def _create_indexes(self) -> None:
        """Create DB indexes for better performance."""
        with self._conn:
            # Index for repository 'path'
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_repositories_path
                ON repositories(path)
            """)
            # Composite index for files (repo_id, path)
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_repo_path
                ON files(repo_id, path)
            """)

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        """Get the database connection, ensuring it's valid."""
        self._ensure_connection()
        return self._conn

    def _ensure_connection(self) -> None:
        """Verify the DB connection is healthy, re-initialize if needed."""
        if not self._conn:
            self.initialize()
            return
        try:
            self._conn.execute("SELECT 1")
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            self._conn = None
            self.initialize()

    def insert_message(self, message: str) -> None:
        """Insert a message into the messages table."""
        self._ensure_connection()
        if not self._conn:
            raise RuntimeError("Database not initialized.")
        with self._conn:
            self._conn.execute(
                "INSERT INTO messages (message, created_at) VALUES (?, ?)",
                (message, datetime.now().isoformat())
            )

    def insert_repository(self, path: str, total_files: int, total_size: int) -> int:
        """Insert or update repository info, returns repo_id."""
        self._ensure_connection()
        if not self._conn:
            raise RuntimeError("Database not initialized.")
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

    def insert_file(self,
                    repo_id: int,
                    path: str,
                    size: int,
                    content: Optional[str] = None,
                    token_count: Optional[int] = None) -> None:
        """Insert or update a single file record."""
        self._ensure_connection()
        if not self._conn:
            raise RuntimeError("Database not initialized.")
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

    def insert_files_batch(self,
                           repo_id: int,
                           files_data: List[Dict[str, Any]]) -> None:
        """
        Batch insert or update multiple file records for improved performance.
        files_data should contain dicts with 'path', 'size', optional 'content'/'token_count'.
        """
        self._ensure_connection()
        if not self._conn:
            raise RuntimeError("Database not initialized.")
        now_str = datetime.now().isoformat()
        with self._conn:
            self._conn.executemany("""
                INSERT INTO files (repo_id, path, size, content, token_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_id, path) DO UPDATE SET
                    size=excluded.size,
                    content=excluded.content,
                    token_count=excluded.token_count,
                    updated_at=excluded.updated_at
            """, [
                (
                    repo_id,
                    f['path'],
                    f['size'],
                    f.get('content'),
                    f.get('token_count'),
                    now_str,
                    now_str
                )
                for f in files_data
            ])

    def cleanup_old_data(self, days: int = 30) -> None:
        """
        Remove old messages from the 'messages' table if older than 'days'.
        Useful for preventing unbounded growth.
        """
        self._ensure_connection()
        if not self._conn:
            raise RuntimeError("Database not initialized.")
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self._conn:
            self._conn.execute(
                "DELETE FROM messages WHERE created_at < ?",
                (cutoff,)
            )


def get_db() -> SQLiteDB:
    """Get or create the SQLite singleton instance."""
    manager = get_manager()
    db = manager.get('sqlite')

    if not db:
        db = SQLiteDB()
        manager.register('sqlite', db)
        db.initialize()

    return db
