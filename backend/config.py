import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "FinSight"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database: In Vercel serverless environment root is read-only, default to /tmp
    default_sqlite: str = "sqlite:////tmp/finsight.db" if os.getenv("VERCEL") == "1" else "sqlite:///./finsight.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", default_sqlite)
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "finsight-super-secret-production-key-2026-pk")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Environment & Demo Seeding (Disabled by default in production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")
    
    # Currency & Localization Defaults for Pakistani FMCG / B2B market
    DEFAULT_CURRENCY: str = "PKR"
    DEFAULT_TAX_RATE: float = 0.0  # Common default for wholesale goods (can be set per invoice)

settings = Settings()
