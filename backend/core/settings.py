"""Application-level settings for auth, CORS, and app metadata."""
import os

from backend.core import env


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    """Server host/port, CORS origins, session secret key."""

    APP_NAME = os.getenv('APP_NAME')
    APP_VERSION = os.getenv('APP_VERSION')
    SECRET_KEY = os.getenv('SECRET_KEY')

    HOST = os.getenv('APP_HOST', '0.0.0.0')
    PORT = int(os.getenv('APP_PORT', '8001'))

    ALLOWED_ORIGINS = _split_csv(os.getenv('ALLOWED_ORIGINS', ''))


settings = Settings()
