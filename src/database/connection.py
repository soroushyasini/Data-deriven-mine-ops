"""
Database connection management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from src.database.models import Base


class DatabaseConnection:
    """Manages database connections."""
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection.
        
        Args:
            db_url: Database URL (default from environment)
        """
        if db_url is None:
            db_url = os.getenv(
                'DATABASE_URL',
                'postgresql://postgres:postgres@localhost:5432/mining_ops'
            )
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.
        
        Yields:
            SQLAlchemy Session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global instance
_db_connection = None


def get_db() -> DatabaseConnection:
    """Get or create global database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def init_database(db_url: str = None):
    """
    Initialize database - create tables.
    
    Args:
        db_url: Database URL
    """
    db = DatabaseConnection(db_url)
    db.create_tables()
    print("Database tables created successfully")
    return db
