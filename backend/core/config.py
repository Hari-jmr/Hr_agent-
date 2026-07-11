"""Odoo DB + RAG configuration — all values sourced from environment."""
import os

from backend.core import env


class Config:
    """Odoo DB credentials and RAG pipeline settings."""

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
