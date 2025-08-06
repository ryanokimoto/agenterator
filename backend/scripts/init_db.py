import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.core.config import settings
from app.models.user import Base

def init_db():
    """Create all database tables"""
    print(f"Creating database tables...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    engine = create_engine(settings.DATABASE_URL)
    
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()