import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _db_url() -> str:
    url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'fasalscan.db'}")
    # Render/Heroku hand out postgres://, SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    APP_NAME = "FasalScan"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-in-production")
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
    DATABASE_URL = _db_url()

    CORS_ORIGINS = _list(os.getenv("CORS_ORIGINS", "*"))

    DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@fasalscan.app")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")
    DEMO_NAME = os.getenv("DEMO_NAME", "Demo Grower")

    # Vision model (YOLOv8 exported to ONNX)
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "best.onnx"))
    CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.35"))
    IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.45"))
    # Per-class overrides keyed as "<state>_<fruit>", e.g. {"rotten_banana": 0.85}
    CLASS_THRESHOLDS: dict[str, float] = json.loads(
        os.getenv("CLASS_THRESHOLDS", '{"rotten_banana": 0.6}')
    )
    # Only used if the ONNX file has no "names" metadata (Ultralytics exports include it)
    CLASS_NAMES = _list(os.getenv("CLASS_NAMES", ""))
    # Extra passes on overlapping tiles so many small fruit in one photo are still found
    TILED_INFERENCE = os.getenv("TILED_INFERENCE", "1") == "1"
    MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "8"))
    MAX_IMAGE_SIDE = int(os.getenv("MAX_IMAGE_SIDE", "1280"))

    # Weather (Open-Meteo, no key needed). Default: Mingora, Swat
    DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "34.7717"))
    DEFAULT_LON = float(os.getenv("DEFAULT_LON", "72.3602"))

    # Open-weight LLM + Whisper served through Groq's OpenAI-compatible API.
    # Leave GROQ_API_KEY empty and the app falls back to built-in templates.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    ASR_MODEL = os.getenv("ASR_MODEL", "whisper-large-v3-turbo")
    LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "20"))


settings = Settings()
