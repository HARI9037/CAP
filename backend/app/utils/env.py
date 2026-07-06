import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"
ENV_KEYS = (
    "APP_NAME",
    "APP_VERSION",
    "LOG_LEVEL",
    "DEMO_MODE",
    "DATABASE_URL",
    "CAP_DB_PATH",
    "CORS_ORIGINS",
    "GROQ_API_KEY",
    "GROQ_API_URL",
    "GROQ_MODEL",
    "GROQ_MAX_TOKENS",
    "GROQ_TIMEOUT_SECONDS",
    "CLERK_JWKS_URL",
    "CLERK_ISSUER",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
)
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://cap-mvp.vercel.app",
)
PLACEHOLDER_ENV_VALUES = {"<Render Secret>"}


def _clean_env_value(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    if value in PLACEHOLDER_ENV_VALUES:
        return None
    return value


def load_environment() -> None:
    file_values = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}

    for key in ENV_KEYS:
        process_value = _clean_env_value(os.getenv(key))
        file_value = _clean_env_value(file_values.get(key))
        value = process_value or file_value

        if value is not None:
            os.environ[key] = value
        elif key in os.environ and not os.environ[key].strip():
            os.environ.pop(key, None)


def _env_value(key: str) -> str | None:
    return _clean_env_value(os.getenv(key))


def _as_bool(raw_value: str | None, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_cors_origins(raw_value: str | None) -> list[str]:
    origins = list(DEFAULT_CORS_ORIGINS)
    if not raw_value:
        return origins
    for origin in raw_value.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)
    return origins


def _resolve_db_path(raw_value: str | None) -> Path:
    if not raw_value:
        return (BASE_DIR / "data" / "cap.db").resolve()
    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate
    return (BASE_DIR / candidate).resolve()


def _as_float(raw_value: str | None, default: float) -> float:
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _as_int(raw_value: str | None, default: int) -> int:
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    log_level: str
    demo_mode: bool
    db_path: Path
    cors_origins: list[str]
    database_url: str | None = None
    groq_api_key: str | None = None
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "openai/gpt-oss-20b"
    groq_max_tokens: int = 8192
    groq_timeout_seconds: float = 20.0
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"


def get_settings() -> Settings:
    """Build settings from the current process environment.

    Call :func:`load_environment` (or :func:`initialize_settings`) before this
    in application code so values from ``backend/.env`` are present.
    """
    return Settings(
        app_name=_env_value("APP_NAME") or "CAP Backend",
        app_version=_env_value("APP_VERSION") or "0.1.0",
        log_level=_env_value("LOG_LEVEL") or "INFO",
        demo_mode=_as_bool(_env_value("DEMO_MODE"), default=False),
        database_url=_env_value("DATABASE_URL"),
        db_path=_resolve_db_path(_env_value("CAP_DB_PATH")),
        cors_origins=_parse_cors_origins(_env_value("CORS_ORIGINS")),
        groq_api_key=_env_value("GROQ_API_KEY"),
        groq_api_url=(
            _env_value("GROQ_API_URL")
            or "https://api.groq.com/openai/v1/chat/completions"
        ),
        groq_model=_env_value("GROQ_MODEL") or "openai/gpt-oss-20b",
        groq_max_tokens=_as_int(_env_value("GROQ_MAX_TOKENS"), default=8192),
        groq_timeout_seconds=_as_float(
            _env_value("GROQ_TIMEOUT_SECONDS"),
            default=20.0,
        ),
        clerk_jwks_url=_env_value("CLERK_JWKS_URL"),
        clerk_issuer=_env_value("CLERK_ISSUER"),
        supabase_url=_env_value("SUPABASE_URL"),
        supabase_service_role_key=_env_value("SUPABASE_SERVICE_ROLE_KEY"),
        openai_api_key=_env_value("OPENAI_API_KEY"),
        openai_model=_env_value("OPENAI_MODEL") or "gpt-5.5",
    )


def initialize_settings() -> Settings:
    """Load ``backend/.env`` once for this process, then return application settings."""
    load_environment()
    return get_settings()
