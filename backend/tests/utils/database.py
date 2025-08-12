"""
Database utilities for testing.
"""
from typing import Optional, List, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import Base


class TestDatabase:
    """Test database manager."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize test database.
        
        Args:
            database_url: Database URL (uses in-memory SQLite by default)
        """
        self.database_url = database_url or "sqlite:///:memory:"
        self.engine = None
        self.SessionLocal = None
    
    def setup(self):
        """Set up test database."""
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {},
            poolclass=StaticPool if "sqlite" in self.database_url else None,
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
    
    def teardown(self):
        """Tear down test database."""
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
            self.engine.dispose()
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session with automatic cleanup.
        
        Yields:
            Database session
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
    
    def reset(self):
        """Reset database to clean state."""
        self.teardown()
        self.setup()
    
    def truncate_all_tables(self, except_tables: Optional[List[str]] = None):
        """
        Truncate all tables except specified ones.
        
        Args:
            except_tables: List of table names to skip
        """
        except_tables = except_tables or []
        
        with self.engine.connect() as conn:
            # Get all table names
            inspector = self.engine.inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Disable foreign key checks for SQLite
            if "sqlite" in self.database_url:
                conn.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Truncate tables
            for table in tables:
                if table not in except_tables:
                    if "sqlite" in self.database_url:
                        conn.execute(text(f"DELETE FROM {table}"))
                    else:
                        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            
            # Re-enable foreign key checks
            if "sqlite" in self.database_url:
                conn.execute(text("PRAGMA foreign_keys = ON"))
            
            conn.commit()
    
    def seed_data(self, fixtures: Dict[str, List[Any]]):
        """
        Seed database with fixture data.
        
        Args:
            fixtures: Dict of model_name -> list of instances
        """
        with self.get_session() as session:
            for model_name, instances in fixtures.items():
                for instance in instances:
                    session.add(instance)
            session.commit()
    
    def count_records(self, model) -> int:
        """
        Count records in a table.
        
        Args:
            model: SQLAlchemy model class
        
        Returns:
            Number of records
        """
        with self.get_session() as session:
            return session.query(model).count()
    
    def execute_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """
        Execute raw SQL query.
        
        Args:
            sql: SQL query
            params: Query parameters
        
        Returns:
            Query result
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            conn.commit()
            return result.fetchall()