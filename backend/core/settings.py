import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    """Application-level config (auth, CORS, app metadata)."""
    def __init__(self) -> None:
        self.APP_NAME = os.getenv('APP_NAME', 'JMR HR Agent API')
        self.APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
        self.HOST = os.getenv('APP_HOST', '0.0.0.0')
        self.PORT = int(os.getenv('APP_PORT', '8001'))
        self.ALLOWED_ORIGINS = _split_csv(
            os.getenv(
                'ALLOWED_ORIGINS',
                'http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:8001,http://localhost:8001',
            )
        )


settings = Settings()
