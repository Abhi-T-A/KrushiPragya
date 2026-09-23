import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.core.config import settings
from app.api.v1.health import get_health_check_db

client = TestClient(app)


def test_health_check():
    """Verify GET /api/v1/health returns 200 and expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "KrushiPragya"
    assert data["version"] == settings.APP_VERSION


def test_database_health_unconfigured():
    """Verify GET /api/v1/health/database gracefully returns 503 when DB is unconfigured."""
    if not settings.is_database_configured:
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"


def test_database_health_mocked_connected():
    """Verify GET /api/v1/health/database returns 200 when database executes successfully."""
    mock_db = MagicMock()
    mock_db.execute.return_value = None

    # Override get_health_check_db dependency
    app.dependency_overrides[get_health_check_db] = lambda: mock_db
    try:
        # Temporarily pretend DB is configured for this unit test
        original_config = settings.DATABASE_URL
        settings.DATABASE_URL = "postgresql://mock_user:mock_pass@localhost:5432/mock_db"

        response = client.get("/api/v1/health/database")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    finally:
        settings.DATABASE_URL = original_config
        app.dependency_overrides.pop(get_health_check_db, None)


@pytest.mark.skipif(
    not settings.is_database_configured,
    reason="Live database not configured; skipping integration test",
)
def test_live_database_health():
    """Test live database connectivity when DATABASE_URL is configured."""
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
