# from threading import Lock

# import asyncpg
# from typing import Optional, List, Dict, Any
# import datetime


# class PostgresClient:
#     def __init__(self, dsn: str, min_size: int = 5, max_size: int = 20):
#         self.dsn = dsn
#         self.min_size = min_size
#         self.max_size = max_size
#         self.pool: Optional[asyncpg.Pool] = None

#     async def connect(self):
#         if self.pool is None:
#             self.pool = await asyncpg.create_pool(
#                 dsn=self.dsn, min_size=self.min_size, max_size=self.max_size
#             )

#     async def execute(self, query: str, *args) -> str:
#         if not self.pool:
#             raise RuntimeError("Postgres client not connected")

#         async with self.pool.acquire() as conn:
#             return await conn.execute(query, *args)

#     async def transaction(self):
#         if not self.pool:
#             raise RuntimeError("Postgres client not connected")

#         conn = await self.pool.acquire()
#         tx = conn.transaction()
#         await tx.start()

#         return conn, tx

#     async def close(self):
#         if self.pool:
#             await self.pool.close()
#             self.pool = None


# # --------------------------------
# # Singleton Management
# # --------------------------------
# _clients: Dict[str, Optional[PostgresClient]] = {}
# _lock = Lock()

# async def init_postgres_client(
#     name: str,
#     dsn: str,
#     min_size: int = 1,
#     max_size: int = 10,
# ) -> PostgresClient:
#     with _lock:
#         if name in _clients:
#             return _clients[name]

#         client = PostgresClient(
#             dsn=dsn,
#             min_size=min_size,
#             max_size=max_size,
#         )
#         _clients[name] = client

#     await client.connect()
#     return client


# def get_postgres_client(name: str) -> PostgresClient:
#     if name not in _clients:
#         raise RuntimeError("Postgres client not initialized.")
#     return _clients[name]


# async def close_postgres_client(name: str):
#     with _lock:
#         client = _clients.pop(name, None)

#     if client:
#         await client.close()


from threading import Lock
from typing import Optional

import asyncpg


class _PostgresConnection:
    def __init__(self, dsn: str, min_size: int, max_size: int):
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """
        Create the PostgreSQL connection pool.
        """
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )

    async def execute(self, query: str, *args) -> str:
        """
        Execute a SQL statement.
        """
        if self._pool is None:
            raise RuntimeError("Postgres client is not connected.")

        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """
        Execute a query and return all rows.
        """
        if self._pool is None:
            raise RuntimeError("Postgres client is not connected.")

        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        Execute a query and return a single row.
        """
        if self._pool is None:
            raise RuntimeError("Postgres client is not connected.")

        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """
        Execute a query and return a single value.
        """
        if self._pool is None:
            raise RuntimeError("Postgres client is not connected.")

        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def transaction(self):
        """
        Start a transaction.

        Returns:
            tuple[asyncpg.Connection, asyncpg.Transaction]
        """
        if self._pool is None:
            raise RuntimeError("Postgres client is not connected.")

        conn = await self._pool.acquire()
        tx = conn.transaction()
        await tx.start()

        return conn, tx

    async def release(self, conn: asyncpg.Connection) -> None:
        """
        Release a connection acquired via transaction().
        """
        if self._pool is not None:
            await self._pool.release(conn)

    async def close(self) -> None:
        """
        Close the PostgreSQL connection pool.
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


class PostgresClient:
    _clients: dict[str, _PostgresConnection] = {}
    _lock = Lock()

    @classmethod
    async def init(cls, name: str, dsn: str, min_size: int = 1, max_size: int = 10) -> _PostgresConnection:
        """
        Initialize and register a PostgreSQL connection pool.

        Raises:
            RuntimeError: If the client has already been initialized.
        """
        with cls._lock:
            if name in cls._clients:
                raise RuntimeError(
                    f"Postgres client '{name}' is already initialized."
                )

        client = _PostgresConnection(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
        )

        await client.connect()

        with cls._lock:
            cls._clients[name] = client

        return client

    @classmethod
    def get(cls, name: str) -> _PostgresConnection:
        """
        Retrieve a PostgreSQL client by name.
        """
        if name not in cls._clients:
            raise RuntimeError(
                f"Postgres client '{name}' is not initialized."
            )

        return cls._clients[name]

    @classmethod
    async def shutdown(cls, name: str) -> None:
        """
        Close and remove a PostgreSQL client.
        """
        with cls._lock:
            client = cls._clients.pop(name, None)

        if client:
            await client.close()

    @classmethod
    async def shutdown_all(cls) -> None:
        """
        Close and remove all PostgreSQL clients.
        """
        with cls._lock:
            clients = list(cls._clients.values())
            cls._clients.clear()

        for client in clients:
            await client.close()

