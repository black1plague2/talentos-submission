import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))
PORT: int = int(os.getenv("PORT", "8000"))

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ML_DIR = BASE_DIR / "ml"
OUTPUT_DIR = BASE_DIR / "output"
MODEL_PATH = ML_DIR / "ranker_model.pkl"
