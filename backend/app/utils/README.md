# utils/

## Purpose

Shared backend utilities for environment loading and logging.

## Responsibilities

`env.py`

- Reads `backend/.env` with `dotenv_values`.
- Falls back to process environment variables.
- Cleans blank values.
- Parses booleans, floats, CORS origins, and database paths.
- Exposes a frozen `Settings` dataclass.
- Exposes `initialize_settings()` for app startup.

`logging.py`

- Uses Python standard logging.
- Writes logs to stdout.
- Reads log level from the `LOG_LEVEL` environment variable.

## Rules

- No business logic.
- No Groq API calls.
- No database calls.
