"""
Pytest configuration and fixtures for backend tests.
"""
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime, UTC

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config import Settings
from backend.database.connection import init_database, run_migrations, get_db, DatabaseConnection
from backend.core.security import token_manager, create_token_hash
from backend.main import create_app


@pytest.fixture(scope="function")
def test_db_path(request):
    """Create a temporary database file for testing."""
    # Use test function name to create unique database file
    test_name = request.node.name.replace('[', '_').replace(']', '_').replace('-', '_')
    with tempfile.NamedTemporaryFile(suffix=f'_{test_name}.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def test_settings(test_db_path):
    """Create test settings with temporary database."""
    return Settings(
        database_path=test_db_path,
        api_token="test-token-12345",
        log_level="DEBUG",
    )


@pytest.fixture(scope="function")
def test_db(test_settings):
    """Initialize a fresh database for each test."""
    db_path = test_settings.database_path
    
    # Delete existing database file to start fresh
    if os.path.exists(db_path):
        os.unlink(db_path)
    
    # Override the database path in settings
    original_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = db_path
    
    # Clear the cached settings so get_settings() picks up the new DATABASE_PATH
    from backend.config import get_settings
    get_settings.cache_clear()
    
    # Reset connection cache
    DatabaseConnection._local = None
    
    # Initialize database
    init_database()
    run_migrations()
    
    yield db_path
    
    # Cleanup
    if original_path:
        os.environ['DATABASE_PATH'] = original_path
    else:
        os.environ.pop('DATABASE_PATH', None)
    DatabaseConnection._local = None
    get_settings.cache_clear()
    
    # Clean up database file
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.fixture(scope="function")
def db_connection(test_db):
    """Get a database connection for direct SQL operations."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def test_token():
    """Generate a test API token."""
    return "test-token-12345"


@pytest.fixture(scope="function")
def auth_headers(test_token):
    """Auth headers for API requests."""
    return {"X-Local-API-Token": test_token}


@pytest.fixture(scope="function")
def app(test_db, test_settings):
    """Create FastAPI app with test settings."""
    original_token = os.environ.get('LOCAL_API_TOKEN')
    os.environ['LOCAL_API_TOKEN'] = test_settings.api_token
    
    # Manually initialize token manager (since lifespan won't run with TestClient)
    from backend.core.security import token_manager, create_token_hash
    from datetime import datetime, UTC
    token_manager._token = test_settings.api_token
    token_manager._token_hash = create_token_hash(test_settings.api_token)
    token_manager._created_at = datetime.now(UTC)
    
    # Create app
    test_app = create_app()
    
    yield test_app
    
    # Cleanup
    if original_token:
        os.environ['LOCAL_API_TOKEN'] = original_token
    else:
        os.environ.pop('LOCAL_API_TOKEN', None)


@pytest.fixture(scope="function")
def client(app):
    """Sync test client."""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def async_client(app):
    """Async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def sample_campaign():
    """Sample campaign data for testing."""
    return {
        "name": "Test Campaign",
        "project": "Test Project",
        "type": "airdrop",
        "network": "Ethereum",
        "description": "Test description",
        "official_url": "https://example.com",
        "campaign_url": "https://example.com/campaign",
        "status": "active",
        "verification_status": "unverified",
        "risk_level": "low",
        "risk_score": 10,
    }


@pytest.fixture(scope="function")
def sample_source():
    """Sample source data for testing."""
    return {
        "name": "Test Source",
        "type": "api",
        "base_url": "https://api.example.com",
        "config": {"key": "value"},
        "rate_limit": 60,
        "timeout": 30,
    }


# Helper functions for tests
def create_test_campaign(db_connection, **kwargs):
    """Create a test campaign in the database."""
    defaults = {
        "id": str(uuid4()),
        "stable_id": f"test_{uuid4().hex[:8]}",
        "name": "Test Campaign",
        "project": "Test Project",
        "type": "airdrop",
        "network": "Ethereum",
        "description": "Test description",
        "official_url": "https://example.com",
        "campaign_url": "https://example.com/campaign",
        "status": "active",
        "verification_status": "unverified",
        "risk_level": "low",
        "risk_score": 10,
        "discovered_at": datetime.now(UTC).isoformat(),
        "last_seen_at": datetime.now(UTC).isoformat(),
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    defaults.update(kwargs)
    
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    db_connection.execute(
        f"INSERT INTO campaigns ({cols}) VALUES ({placeholders})",
        list(defaults.values())
    )
    db_connection.commit()
    return defaults


def create_test_source(db_connection, **kwargs):
    """Create a test source in the database."""
    defaults = {
        "id": str(uuid4()),
        "name": "Test Source",
        "type": "api",
        "base_url": "https://api.example.com",
        "config": "{}",
        "rate_limit": 60,
        "timeout": 30,
        "status": "enabled",
        "enabled": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    defaults.update(kwargs)
    
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    db_connection.execute(
        f"INSERT INTO sources ({cols}) VALUES ({placeholders})",
        list(defaults.values())
    )
    db_connection.commit()
    return defaults