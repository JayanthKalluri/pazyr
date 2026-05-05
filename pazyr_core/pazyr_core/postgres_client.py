import asyncpg
from typing import Optional, List, Dict, Any
import datetime

class PostgresClient:
    def __init__(self, dsn: str, min_size:int = 5, max_size:int = 20):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
        self.min_size = min_size
        self.max_size = max_size

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn = self.dsn,
            min_size = self.min_size,
            max_size = self.max_size    
        )
    
    async def close(self):
        if self.pool:
            await self.pool.close()

    async def run_query(self, query: str, *args):
        print("Query being executed", query)
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)


