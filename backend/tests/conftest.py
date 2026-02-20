import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.execute = AsyncMock()
    db.scalar = AsyncMock(return_value=0)
    db.delete = AsyncMock()
    db.add = AsyncMock()
    return db
