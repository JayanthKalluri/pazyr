# import redis
# import redis.asyncio as aioredis
# from typing import Dict, Optional
# from threading import Lock

# class RedisClient:
#     def __init__(
#         self,
#         redis_url: str,
#         group: str,
#         max_len: int,
#     ):
#         self.client = aioredis.Redis.from_url(redis_url, decode_responses=True)
#         self.group = group
#         self.max_len = max_len

#     async def push_to_stream(self, stream_name: str, payload: str) -> str:
#         print(f"Pushing into {stream_name} payload={payload}")
#         msg = {"data": payload}
#         return await self.client.xadd(
#             stream_name,
#             msg,
#             maxlen=self.max_len,
#             approximate=True,
#         )

#     async def read_from_stream(
#         self, stream_name: str, consumer: str, count: int = 1, block: int = 0
#     ):
#         response = await self.client.xreadgroup(
#             groupname=self.group,
#             consumername=consumer,
#             streams={stream_name: ">"},
#             count=count,
#             block=block,
#         )

#         if not response:
#             return []

#         messages = []
#         for _, msgs in response:
#             for msg_id, data in msgs:
#                 messages.append((msg_id, data["data"]))

#         return messages

#     async def ack(self, stream_name: str, msg_id: str):
#         await self.client.xack(stream_name, self.group, msg_id)

#     async def create_group_for_stream(self, stream_name: str):
#         try:
#             await self.client.xgroup_create(
#                 name=stream_name,
#                 groupname=self.group,
#                 id="0",
#                 mkstream=True,
#             )
#         except redis.exceptions.ResponseError as e:
#             if "BUSYGROUP" in str(e):
#                 pass
#             else:
#                 raise
#         except Exception as e:
#             raise

#     async def close(self):
#         await self.client.aclose()


# # -------------------------------
# # Singleton Management
# # -------------------------------
# _clients: Dict[str, RedisClient | None] = {}
# _lock = Lock()


# def init_redis_client(name: str, redis_url: str, group: str, max_len: int) -> RedisClient:
#     with _lock:
#         if name in _clients:
#             return _clients[name]

#         redis_client = RedisClient(
#             redis_url=redis_url,
#             group=group,
#             max_len=max_len,
#         )
#         _clients[name] = redis_client
#     return redis_client


# def get_redis_client(name: str) -> RedisClient:
#     if name not in _clients:
#         raise RuntimeError("Redis client not initialized.")

#     return _clients[name]


# async def close_redis_client(name: str):
#     with _lock:
#         client = _clients.pop(name, None)
    
#     if client:
#         await client.close()
        
        

from threading import Lock

import redis
import redis.asyncio as aioredis


class _RedisConnection:
    def __init__(self, redis_url: str):
        """
        Initialize a Redis client using the provided URL.

        Args:
            redis_url (str): The connection URL for the Redis server.
        """
        self._client = aioredis.Redis.from_url(
            redis_url,
            decode_responses=True,
        )

    @property
    def client(self) -> aioredis.Redis:
        """
        Get the underlying Redis client instance.

        Returns:
            aioredis.Redis: The Redis client object.
        """
        return self._client

    async def publish(self, stream: str, payload: str, max_len: int | None = None) -> str:
        """
        Publish a message to a Redis stream.

        Args:
            stream (str): The name of the Redis stream.
            payload (str): The message payload to publish.
            max_len (int | None, optional): Maximum length of the stream.
                If provided, older entries may be trimmed. Defaults to None.

        Returns:
            str: The ID of the published message.
        """
        kwargs = {}

        if max_len is not None:
            kwargs["maxlen"] = max_len
            kwargs["approximate"] = True

        return await self._client.xadd(
            stream,
            {"data": payload},
            **kwargs,
        )

    async def consume(self, stream: str, group: str, consumer: str, count: int = 1, block: int=0) -> list[tuple[str, str]]:
        """
        Consume messages from a Redis stream using a consumer group.

        Args:
            stream (str): The name of the Redis stream.
            group (str): The consumer group name.
            consumer (str): The consumer name within the group.
            count (int, optional): Maximum number of messages to read. Defaults to 1.
            block (int, optional): Block time in milliseconds. Defaults to 0 (non-blocking).

        Returns:
            list[tuple[str, str]]: A list of (message_id, payload) tuples.
        """
        response = await self._client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: ">"},
            count=count,
            block=block,
        )
        
        if not response:
            return []

        messages = []

        for _, entries in response:
            for message_id, data in entries:
                messages.append(
                    (
                        message_id,
                        data["data"],
                    )
                )

        return messages      

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        """
        Acknowledge a message in a Redis stream.

        Args:
            stream (str): The name of the Redis stream.
            group (str): The consumer group name.
            message_id (str): The ID of the message to acknowledge.
        """
        await self._client.xack(
            stream,
            group,
            message_id,
        )

    async def create_consumer_group(self, stream: str, group: str, start_id: str = "0") -> None:
        """
        Create a consumer group for a Redis stream.

        Args:
            stream (str): The name of the Redis stream.
            group (str): The name of the consumer group.
            start_id (str, optional): The starting ID for the group. Defaults to "0".

        Notes:
            If the group already exists, the BUSYGROUP error is ignored.
        """   
        try:
            await self._client.xgroup_create(
                name=stream,
                groupname=group,
                id=start_id,
                mkstream=True,
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def ping(self) -> bool:
        """
        Ping the Redis server to check connectivity.

        Returns:
            bool: True if the server responds, False otherwise.
        """
        return await self._client.ping()
          
    async def close(self) -> None:
        """
        Close the Redis client connection.
        """
        await self._client.aclose()


class RedisClient:
    _clients: dict[str, _RedisConnection] = {}
    _lock = Lock()
    
    @classmethod
    def init(cls, name: str, redis_url: str) -> _RedisConnection:
        """
        Initialize a new Redis client and register it under the given name.

        Args:
            name (str): The identifier for the Redis client.
            redis_url (str): The connection URL for the Redis server.

        Returns:
            RedisClient: The initialized Redis client instance.

        Raises:
            RuntimeError: If a client with the given name is already initialized.
        """
        with cls._lock:
            if name in cls._clients:
                raise RuntimeError(f"Redis client '{name}' is already initialized.")

            client = _RedisConnection(redis_url)
            cls._clients[name] = client

        return client

    @classmethod
    def get(cls, name: str) -> _RedisConnection:
        """
        Retrieve a Redis client by name.

        Args:
            name (str): The identifier of the Redis client.

        Returns:
            RedisClient: The Redis client instance.

        Raises:
            RuntimeError: If the client with the given name is not initialized.
        """
        if name not in cls._clients:
            raise RuntimeError("Redis client '{name}' is not initialized.")
        
        return cls._clients[name]

    @classmethod
    async def shutdown(cls, name: str):
        """
        Shut down and remove a Redis client by name.

        Args:
            name (str): The identifier of the Redis client to shut down.

        Notes:
            If the client does not exist, nothing happens.
        """
        with cls._lock:
            client = cls._clients.pop(name, None)

        if client:
            await client.close()

    @classmethod
    async def shutdown_all(cls) -> None:
        """
        Shut down and remove all Redis clients.

        Notes:
            All registered clients are closed and cleared from the manager.
        """
        with cls._lock:
            clients = list(cls._clients.values())
            cls._clients.clear()

        for client in clients:
            await client.close()
  
