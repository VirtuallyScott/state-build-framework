"""
Database connection and operations for the Build State API.
"""
import redis
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Database:
    """Database connection manager supporting SQLite and PostgreSQL."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.redis_client = redis.from_url(settings.redis_url) if settings.cache_enabled else None

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        db_session = self.get_session()
        try:
            yield db_session
        finally:
            db_session.close()

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
    """Initialize database with dummy data in development environment."""
    if settings.environment == "development":
        dummy_data_file = "dummy-data.sql"
        try:
            with open(dummy_data_file, 'r') as f:
                dummy_sql = f.read()
            
            with db.get_connection() as conn:
                conn.execute(text(dummy_sql))
                conn.commit()

            print("Dummy data loaded successfully")

        except Exception as e:
            print(f"Error loading dummy data: {e}")
            raise
    else:
        print("Database initialized (production mode - no dummy data)")