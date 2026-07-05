from fastapi.testclient import TestClient

from app.utils.env import Settings
from main import create_app


def _settings(db_path):
    return Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=db_path,
        cors_origins=[
            "http://localhost:5173",
            "https://cap-mvp-v2.vercel.app",
        ],
        groq_api_key="test-key",
    )


def test_chat_preflight_allows_configured_origin_and_auth_headers(tmp_path):
    app = create_app(settings=_settings(tmp_path / "cors.db"))

    with TestClient(app) as client:
        response = client.options(
            "/chat",
            headers={
                "Origin": "https://cap-mvp-v2.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

    assert response.status_code in (200, 204)
    assert response.headers.get(
        "access-control-allow-origin") == "https://cap-mvp-v2.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"

    allowed_headers = (response.headers.get(
        "access-control-allow-headers") or "").lower()
    assert "authorization" in allowed_headers or allowed_headers == "*"

    allowed_methods = (response.headers.get(
        "access-control-allow-methods") or "").upper()
    assert "POST" in allowed_methods or allowed_methods == "*"


def test_chat_post_includes_cors_headers_on_auth_error(tmp_path):
    app = create_app(settings=_settings(tmp_path / "cors-post.db"))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"Origin": "https://cap-mvp-v2.vercel.app"},
            json={"message": "hello"},
        )

    assert response.status_code == 401
    assert response.headers.get(
        "access-control-allow-origin") == "https://cap-mvp-v2.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"
