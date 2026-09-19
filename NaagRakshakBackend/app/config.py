import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

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
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_Wzmd94KELvwC@ep-polished-cloud-azi8hzm2-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?ssl=require"
    SQLITE_URL: str = "sqlite+aiosqlite:///./naagrakshak.db"

    # API Keys (Loaded strictly from environment / .env file)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    VERTEX_CREDENTIALS_PATH: str = os.getenv("VERTEX_CREDENTIALS_PATH", "")
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_TTS_URL: str = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")

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
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"

settings = Settings()

