from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Upload Settings
    UPLOAD_DIR: str 
    MAX_UPLOAD_SIZE: int 
    
    # App Settings
    PROJECT_NAME: str = "Masjid Receipts API"
    VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


def get_settings():
    """Compatibility helper for code that imports `get_settings`.
    """
    return settings
