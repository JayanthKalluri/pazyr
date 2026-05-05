import redis
import redis.asyncio as aioredis
from typing import Optional


class RedisClient:
    def __init__(
        self,
        redis_url: str,
        group: str,
        max_len: int,
    ):
        self.client = aioredis.Redis.from_url(redis_url, decode_responses=True)
        self.group = group
        self.max_len = max_len

    async def push_to_stream(self, stream_name: str, payload: str) -> str:
        msg = {"data": payload}
        return await self.client.xadd(
            stream_name,
            msg,
            maxlen=self.max_len,
            approximate=True,
        )

    async def read_from_stream(
        self, stream_name: str, consumer: str, count: int = 1, block: int = 0
    ):
        response = await self.client.xreadgroup(
            groupname=self.group,
            consumername=consumer,
            streams={stream_name: ">"},
            count=count,
            block=block,
        )

        if not response:
            return []

        messages = []
        for _, msgs in response:
            for msg_id, data in msgs:
                messages.append((msg_id, data["data"]))

        return messages

    async def ack(self, stream_name: str, msg_id: str):
        await self.client.xack(stream_name, self.group, msg_id)

    async def create_group_for_stream(self, stream_name: str):
        try:
            await self.client.xgroup_create(
                name=stream_name,
                groupname=self.group,
                id="0",
                mkstream=True,
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                pass
            else:
                raise
        except Exception as e:
            raise

    async def close(self):
        await self.client.aclose()


# -------------------------------
# Singleton Management
# -------------------------------
_redis_client: Optional[RedisClient] = None


def init_redis_client(redis_url: str, group: str, max_len: int) -> RedisClient:
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient(
            redis_url=redis_url,
            group=group,
            max_len=max_len,
        )

    return _redis_client


def get_redis_client() -> RedisClient:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized.")

    return _redis_client


async def close_redis_client():
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
