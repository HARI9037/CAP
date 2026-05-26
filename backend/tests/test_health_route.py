from fastapi.testclient import TestClient

from app.utils.env import Settings
from main import create_app


def test_health_endpoint_reports_ready(tmp_path):
    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=tmp_path / "cap.db",
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert payload["demo_mode"] is False
