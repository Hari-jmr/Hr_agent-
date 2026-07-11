"""All application configuration — sourced from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env before reading any env vars
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / '.env')
load_dotenv(Path(__file__).resolve().parent.parent / '.env')


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


class Config:
    """All application settings."""

    # App runtime
    APP_NAME = os.getenv('APP_NAME')
    APP_VERSION = os.getenv('APP_VERSION')
    SECRET_KEY = os.getenv('SECRET_KEY')
    HOST = os.getenv('APP_HOST', '0.0.0.0')
    PORT = int(os.getenv('APP_PORT', '8001'))
    ALLOWED_ORIGINS = _split_csv(os.getenv('ALLOWED_ORIGINS', ''))

    # Odoo DB (login auth)
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', '')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # RAG / OpenRouter
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_LLM_MODEL = os.getenv('OPENROUTER_LLM_MODEL')
    OPENROUTER_EMBED_MODEL = os.getenv('OPENROUTER_EMBED_MODEL')
    DATABASE_URL = os.getenv('DATABASE_URL')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '512'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '64'))
    TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', '5'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))


config = Config()
