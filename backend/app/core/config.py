from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agenterator"
    DATABASE_URL: str = "postgresql://user:password@localhost/ragdb"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
    
settings = Settings()