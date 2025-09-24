"""
Database connection management for ESG reasoning project.
Handles PostgreSQL connection, session management, and database initialization.
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from src.utils.config import config
from src.database.models import Base, create_tables

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize database connection"""
        try:
            # Create engine with connection pool settings
            self.engine = create_engine(
                config.database.url,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
                echo=False  # Set to True for SQL query logging
            )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Ensure pgvector extension is available
            self._setup_extensions()

            # Create tables if they don't exist
            create_tables(self.engine)
            logger.info("Database tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def _setup_extensions(self):
        """Setup required PostgreSQL extensions"""
        try:
            with self.engine.connect() as conn:
                # Enable pgvector extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("PostgreSQL extensions setup completed")
        except Exception as e:
            logger.warning(f"Could not setup extensions: {e}")

    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_session_direct(self) -> Session:
        """Get a database session (manual management required)"""
        return self.SessionLocal()

    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
def get_db_session():
    """Get database session - use with context manager"""
    return db_manager.get_session()


def get_db_session_direct():
    """Get database session - manual management"""
    return db_manager.get_session_direct()


def check_db_health():
    """Check database health"""
    return db_manager.health_check()


# Collection-specific table names
def get_collection_table_name(base_name: str) -> str:
    """Get collection-specific table name"""
    return f"{config.database.collection_name}_{base_name}"


class CollectionManager:
    """Manages collection-specific operations"""

    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or config.database.collection_name

    def create_collection_tables(self):
        """Create collection-specific tables"""
        # Update table names to include collection prefix
        for table in Base.metadata.tables.values():
            original_name = table.name
            table.name = f"{self.collection_name}_{original_name}"

        # Create tables with new names
        Base.metadata.create_all(db_manager.engine)
        logger.info(f"Created tables for collection: {self.collection_name}")

    def drop_collection_tables(self):
        """Drop collection-specific tables"""
        with db_manager.engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                table_name = f"{self.collection_name}_{table.name}"
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            conn.commit()
        logger.info(f"Dropped tables for collection: {self.collection_name}")

    def collection_exists(self) -> bool:
        """Check if collection tables exist"""
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        collection_tables = [t for t in tables if t.startswith(f"{self.collection_name}_")]
        return len(collection_tables) > 0