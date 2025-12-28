"""Order test configs"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from order_service.orders import app, get_db
from order_service.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    """Creates a new instance of App"""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # hand the client to the test
        yield c
        # --- teardown happens when the 'with' block exits ---

@pytest.fixture
def mock_rabbitmq():
    """Fixture that mocks RabbitMQ for all tests that need it"""
    with patch('order_service.orders.get_exchange') as mock_get_exchange:
        mock_conn = AsyncMock()
        mock_ch = AsyncMock()
        mock_ex = AsyncMock()
        mock_get_exchange.return_value = (mock_conn, mock_ch, mock_ex)
        yield mock_get_exchange
