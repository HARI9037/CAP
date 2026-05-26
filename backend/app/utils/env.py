import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _as_bool(raw_value: str | None, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_cors_origins(raw_value: str | None) -> list[str]:
    if not raw_value:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def _resolve_db_path(raw_value: str | None) -> Path:
    if not raw_value:
        return (BASE_DIR / "data" / "cap.db").resolve()
    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate
    return (BASE_DIR / candidate).resolve()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    log_level: str
    demo_mode: bool
    db_path: Path
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "CAP Backend"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        demo_mode=_as_bool(os.getenv("DEMO_MODE"), default=False),
        db_path=_resolve_db_path(os.getenv("CAP_DB_PATH")),
        cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
