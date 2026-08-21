import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "NaagRakshak Backend API"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "7044"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "naagrakshak"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:7044@localhost:5432/naagrakshak"
    SQLITE_URL: str = "sqlite+aiosqlite:///./naagrakshak.db"

    # API Keys
    OPENAI_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""

    # Model Storage Paths
    MODEL_ONNX_PATH: str = "models/snake_model.onnx"
    CLASS_MAPPING_PATH: str = "models/class_mapping.csv"
    SPECIES_DATA_PATH: str = "models/indian_snakes.csv"

    # Ingestion & Validation Caps
    MAX_PAYLOAD_BYTES: int = 15 * 1024 * 1024  # 15 MB
    MIN_IMAGE_RES: int = 224
    MAX_IMAGE_PIXELS: int = 89478485

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
