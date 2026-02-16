"""
Comprehensive API & E2E Tests
Tests authentication, full CRUD lifecycle, export endpoints, and error handling.
Uses TestClient with an isolated in-memory SQLite database.
"""

import pytest
import os
import uuid
from unittest.mock import patch

# ============ Fixtures ============

@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Ensure test runs against in-memory SQLite and no auth by default"""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_e2e.db")
    monkeypatch.delenv("API_SECRET_KEY", raising=False)


@pytest.fixture
def app():
    """Create fresh FastAPI app for each test"""
    # Force re-import to pick up test env
    import importlib
    import src.core.db_engine as eng
    importlib.reload(eng)

    import src.core.database as db_mod
    importlib.reload(db_mod)
    
    # Create tables
    db_mod.init_db()

    import src.backend.api.main as main_mod
    importlib.reload(main_mod)
    return main_mod.app


@pytest.fixture
def client(app):
    """Create test client (no auth)"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def auth_app(monkeypatch):
    """Create app with auth enabled"""
    monkeypatch.setenv("API_SECRET_KEY", "test-secret-key-123")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_e2e_auth.db")

    import importlib
    import src.core.db_engine as eng
    importlib.reload(eng)

    import src.core.database as db_mod
    importlib.reload(db_mod)
    db_mod.init_db()

    import src.backend.api.auth_middleware as auth_mod
    importlib.reload(auth_mod)

    import src.backend.api.main as main_mod
    importlib.reload(main_mod)
    return main_mod.app


@pytest.fixture
def auth_client(auth_app):
    """Create test client with auth app"""
    from fastapi.testclient import TestClient
    return TestClient(auth_app)


# ============ Health & Root ============

@pytest.mark.api
class TestHealthEndpoints:
    """Test health and root endpoints"""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data

    def test_root_returns_welcome(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "VDO Content API"

    def test_docs_accessible(self, client):
        response = client.get("/docs")
        assert response.status_code == 200


# ============ Authentication ============

@pytest.mark.api
class TestAuthentication:
    """Test API key authentication middleware"""

    def test_public_paths_no_auth_needed(self, auth_client):
        """Health, docs, root should be accessible without key"""
        for path in ["/health", "/", "/docs", "/openapi.json"]:
            resp = auth_client.get(path)
            assert resp.status_code == 200, f"Public path {path} returned {resp.status_code}"

    def test_protected_endpoint_no_key_returns_401(self, auth_client):
        """API endpoints should require key when auth is enabled"""
        resp = auth_client.get("/api/projects")
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_API_KEY"

    def test_protected_endpoint_wrong_key_returns_403(self, auth_client):
        """Wrong API key should return 403"""
        resp = auth_client.get(
            "/api/projects",
            headers={"X-API-Key": "wrong-key"}
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"]["code"] == "INVALID_API_KEY"

    def test_protected_endpoint_valid_header_key(self, auth_client):
        """Valid key via header should work"""
        resp = auth_client.get(
            "/api/projects",
            headers={"X-API-Key": "test-secret-key-123"}
        )
        # Should succeed (200) or 503 if DB not available — NOT 401/403
        assert resp.status_code not in [401, 403]

    def test_protected_endpoint_valid_query_key(self, auth_client):
        """Valid key via query param should work"""
        resp = auth_client.get("/api/projects?api_key=test-secret-key-123")
        assert resp.status_code not in [401, 403]

    def test_no_auth_when_key_not_configured(self, client):
        """When API_SECRET_KEY is empty, all endpoints should be open"""
        resp = client.get("/api/projects")
        # Should not get auth errors
        assert resp.status_code not in [401, 403]


# ============ Project CRUD Lifecycle ============

@pytest.mark.api
@pytest.mark.integration
class TestProjectCRUDLifecycle:
    """Test full create → read → update → delete cycle via API"""

    def test_full_lifecycle(self, client):
        """Complete project lifecycle through API"""
        # 1. Create
        create_data = {
            "title": "E2E Test Project",
            "topic": "Testing full lifecycle",
            "description": "Created via E2E test",
            "target_duration": 30
        }
        resp = client.post("/api/projects", json=create_data)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        project_id = data["data"]["project_id"]

        # 2. Read
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        project = resp.json()
        assert project["title"] == "E2E Test Project"

        # 3. Update
        update_data = {
            "title": "Updated E2E Project",
            "status": "step3_script",
            "workflow_step": 3
        }
        resp = client.patch(f"/api/projects/{project_id}", json=update_data)
        assert resp.status_code == 200

        # Verify update
        resp = client.get(f"/api/projects/{project_id}")
        updated = resp.json()
        assert updated["title"] == "Updated E2E Project"

        # 4. Delete
        resp = client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 5. Verify deleted
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 404

    def test_list_projects(self, client):
        """Test listing projects"""
        # Create two projects
        for title in ["List Test A", "List Test B"]:
            client.post("/api/projects", json={"title": title, "topic": "test"})

        resp = client.get("/api/projects")
        assert resp.status_code == 200
        projects = resp.json()
        assert isinstance(projects, list)
        assert len(projects) >= 2

    def test_create_minimal_project(self, client):
        """Test creating project with minimal fields"""
        resp = client.post("/api/projects", json={
            "title": "Minimal",
            "topic": "min"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_get_nonexistent_returns_404(self, client):
        """Test getting a non-existent project"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/projects/{fake_id}")
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        """Test deleting a non-existent project"""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/api/projects/{fake_id}")
        assert resp.status_code == 404


# ============ Export Endpoints ============

@pytest.mark.api
class TestExportEndpoints:
    """Test export endpoints"""

    def test_export_zip_nonexistent(self, client):
        """ZIP export of non-existent project"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/export/{fake_id}/zip")
        assert resp.status_code in [404, 500]

    def test_export_prompts_nonexistent(self, client):
        """Prompts export of non-existent project"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/export/{fake_id}/prompts")
        assert resp.status_code in [404, 500]


# ============ Error Handling ============

@pytest.mark.api
class TestErrorHandling:
    """Test error responses"""

    def test_invalid_json_body(self, client):
        """Malformed JSON should return 422"""
        resp = client.post(
            "/api/projects",
            content="not-json",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422

    def test_missing_required_fields(self, client):
        """Missing title should return 422"""
        resp = client.post("/api/projects", json={"topic": "no title"})
        assert resp.status_code == 422
