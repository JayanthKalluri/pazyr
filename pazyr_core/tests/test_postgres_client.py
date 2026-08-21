import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pazyr_core.clients.postgres_client import PostgresClient


@pytest.fixture(autouse=True)
def clear_postgres_clients():
    yield
    PostgresClient._clients.clear()


def test_postgres_client_init_and_shutdown():
    mock_pool = Mock()
    mock_pool.close = AsyncMock()

    async def fake_create_pool(*args, **kwargs):
        return mock_pool

    with patch("pazyr_core.clients.postgres_client.asyncpg.create_pool", new=AsyncMock(side_effect=fake_create_pool)) as patched_create_pool:
        client = asyncio.run(PostgresClient.init("test", "postgres://localhost/db", min_size=1, max_size=5))
        assert client is PostgresClient.get("test")
        patched_create_pool.assert_awaited_once_with(dsn="postgres://localhost/db", min_size=1, max_size=5)

    asyncio.run(PostgresClient.shutdown("test"))
    mock_pool.close.assert_awaited_once()
    assert "test" not in PostgresClient._clients


def test_postgres_client_shutdown_all():
    mock_pool_a = Mock()
    mock_pool_a.close = AsyncMock()
    mock_pool_b = Mock()
    mock_pool_b.close = AsyncMock()

    async def fake_create_pool_a(*args, **kwargs):
        return mock_pool_a

    async def fake_create_pool_b(*args, **kwargs):
        return mock_pool_b

    with patch("pazyr_core.clients.postgres_client.asyncpg.create_pool", new=AsyncMock(side_effect=[mock_pool_a, mock_pool_b])):
        asyncio.run(PostgresClient.init("client-a", "postgres://localhost/db_a"))
        asyncio.run(PostgresClient.init("client-b", "postgres://localhost/db_b"))

    asyncio.run(PostgresClient.shutdown_all())
    assert PostgresClient._clients == {}
    mock_pool_a.close.assert_awaited_once()
    mock_pool_b.close.assert_awaited_once()
