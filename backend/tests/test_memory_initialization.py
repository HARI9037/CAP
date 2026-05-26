import sqlite3

from fastapi.testclient import TestClient

from app.utils.env import Settings
from main import create_app


def _count_sessions(db_path):
    with sqlite3.connect(db_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM sessions;").fetchone()[0]


def test_memory_initializes_without_demo_seed(tmp_path):
    db_path = tmp_path / "plain.db"
    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert _count_sessions(db_path) == 0


def test_memory_initializes_with_demo_seed_when_enabled(tmp_path):
    db_path = tmp_path / "seeded.db"
    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=True,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert _count_sessions(db_path) == 1
