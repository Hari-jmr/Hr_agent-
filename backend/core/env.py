from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / '.env'

# Also load backend/.env as fallback
BACKEND_ENV = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(ENV_FILE)
load_dotenv(BACKEND_ENV)
