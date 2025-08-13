import os
from typing import Optional

class Settings:
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net")
    DATABASE_NAME: str = "personal_care_app"
    
    # API Configuration
    API_KEY: str = os.getenv("API_KEY", "pcare_api_key_2024")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # In production, replace with specific origins
    ]
    
    # JWT Configuration (for future authentication)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
