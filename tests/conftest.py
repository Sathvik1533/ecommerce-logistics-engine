import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing testing settings override."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        DATABASE_URL="mysql+pymysql://test_user:test_pass@localhost:3306/test_logistics_db",
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """FastAPI TestClient fixture with overridden settings."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
