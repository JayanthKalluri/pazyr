import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pazyr_core.clients.redis_client import RedisClient


@pytest.fixture(autouse=True)
def clear_redis_clients():
    yield
    RedisClient._clients.clear()


def test_redis_client_init_and_get():
    mock_client = Mock()
    mock_client.xadd = AsyncMock(return_value="message-id")
    mock_client.xreadgroup = AsyncMock(return_value=[("stream1", [("id1", {"data": "payload"})])])
    mock_client.xack = AsyncMock()
    mock_client.xgroup_create = AsyncMock()
    mock_client.aclose = AsyncMock()

    with patch("pazyr_core.clients.redis_client.aioredis.Redis.from_url", return_value=mock_client) as patched_from_url:
        client = RedisClient.init("test", "redis://localhost:6379")
        assert client is RedisClient.get("test")
        patched_from_url.assert_called_once_with("redis://localhost:6379", decode_responses=True)

    async def run_client_ops():
        msg_id = await client.publish("stream", "hello", max_len=10)
        assert msg_id == "message-id"
        mock_client.xadd.assert_awaited_once_with("stream", {"data": "hello"}, maxlen=10, approximate=True)

        messages = await client.consume("stream", "group", "consumer", count=1, block=0, id=">")
        assert messages == [("id1", "payload")]

        await client.ack("stream", "group", "id1")
        mock_client.xack.assert_awaited_once_with("stream", "group", "id1")

        await client.create_consumer_group("stream", "group")
        mock_client.xgroup_create.assert_awaited_once_with(name="stream", groupname="group", id="0", mkstream=True)

    asyncio.run(run_client_ops())

    asyncio.run(RedisClient.shutdown("test"))
    mock_client.aclose.assert_awaited_once()
