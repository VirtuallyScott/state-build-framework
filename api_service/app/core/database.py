"""
Database connection and operations for the Build State API.
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json
from datetime import datetime

from .config import settings


class Database:
    """Database connection manager supporting SQLite and PostgreSQL."""

    def __init__(self):
        self.db_type = self._determine_db_type()
        self.redis_client = redis.from_url(settings.redis_url) if settings.cache_enabled else None

    def _determine_db_type(self) -> str:
        """Determine database type from configuration."""
        if settings.database_type != "auto":
            return settings.database_type

        # Auto-detect from URL
        url = settings.database_url.lower()
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            return "postgresql"
        elif url.startswith("sqlite:///") or url.endswith(".db"):
            return "sqlite"
        else:
            # Default fallback
            return "sqlite"

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(settings.database_url)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
            try:
                yield conn
            finally:
                conn.close()

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
        """Execute a database query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch and (query.strip().upper().startswith("SELECT") or "RETURNING" in query.upper()):
                results = cursor.fetchall()
                return [dict(row) for row in results] if self.db_type == "sqlite" else results
            else:
                conn.commit()
                return []

    def cache_get(self, key: str) -> Optional[str]:
        """Get value from Redis cache."""
        if self.redis_client:
            return self.redis_client.get(key)
        return None

    def cache_set(self, key: str, value: str, ttl: int = None) -> None:
        """Set value in Redis cache."""
        if self.redis_client:
            self.redis_client.set(key, value, ex=ttl or settings.cache_ttl)

    def cache_delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        if self.redis_client:
            self.redis_client.delete(key)


# Global database instance
db = Database()


def init_database():
    """Initialize database schema."""
    schema_file = "init-db.sql"
    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Split on semicolons and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

        for statement in statements:
            if statement:
                db.execute_query(statement, fetch=False)

        print("Database initialized successfully")
    except FileNotFoundError:
        print(f"Warning: {schema_file} not found, skipping database initialization")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise