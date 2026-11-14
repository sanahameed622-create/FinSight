import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "FinSight"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database: Default to local SQLite, easily overridden with PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finsight.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "finsight-super-secret-production-key-2026-pk")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Currency & Localization Defaults for Pakistani FMCG / B2B market
    DEFAULT_CURRENCY: str = "PKR"
    DEFAULT_TAX_RATE: float = 0.0  # Common default for wholesale goods (can be set per invoice)

settings = Settings()
