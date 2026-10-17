import pytest

from app.core.config import Settings


@pytest.mark.unit
def test_default_settings_properties():
    settings = Settings(
        _env_file=None,
        DATABASE_URL=None,
        DB_HOST="db.internal",
        DB_PORT=3306,
        DB_USER="custom_user",
        DB_PASSWORD="custom_password",
        DB_NAME="custom_logistics",
        REDIS_HOST="cache.internal",
        REDIS_PORT=6380,
    )

    assert settings.sync_database_url == (
        "mysql+pymysql://custom_user:custom_password@db.internal:3306/custom_logistics"
    )
    assert settings.redis_connection_url == "redis://cache.internal:6380/0"
    assert settings.celery_broker == "redis://cache.internal:6380/1"
    assert settings.celery_backend == "redis://cache.internal:6380/2"


@pytest.mark.unit
def test_explicit_database_url_override():
    custom_url = "mysql+pymysql://override_user:override_pass@primary.mysql.rds:3306/prod_db"
    settings = Settings(_env_file=None, DATABASE_URL=custom_url)
    assert settings.sync_database_url == custom_url
