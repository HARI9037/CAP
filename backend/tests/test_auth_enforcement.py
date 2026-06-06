from fastapi.testclient import TestClient
from main import create_app
from app.utils.auth import get_current_user_id

def test_unauthenticated_requests_return_401():
    app = create_app()
    with TestClient(app) as client:
        # Chat
        response = client.post("/chat", json={"message": "hello"})
        assert response.status_code == 401

        # Memory
        response = client.get("/memory")
        assert response.status_code == 401
        
        # Settings
        response = client.get("/settings")
        assert response.status_code == 401

def test_authenticated_requests_succeed():
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-id"
    with TestClient(app) as client:
        # Chat (we just expect something other than 401, e.g. 500 if Groq key missing, or 200)
        # We will test settings since it doesn't require an external API
        response = client.get("/settings")
        assert response.status_code == 200
        assert "settings" in response.json()
    app.dependency_overrides.clear()
