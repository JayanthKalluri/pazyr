import os
from typing import List, Dict, Optional

import weaviate
from weaviate.connect import ConnectionParams
from weaviate import WeaviateAsyncClient
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.exceptions import WeaviateBaseError


class WeaviateClient:
    def __init__(self, host: str, http_port: str, grpc_port: str, collection_name: str):
        self.host = host
        self.http_port = http_port
        self.grpc_port = grpc_port
        self.client: Optional[WeaviateAsyncClient] = None
        self.collection_name = collection_name

    async def instantiate_and_connect(self) -> WeaviateAsyncClient:
        api_key = os.getenv("WEAVIATE_SECRET", "")
        if not api_key:
            raise RuntimeError("WEAVIATE_SECRET environment varaible is missing.")

        self.client = weaviate.WeaviateAsyncClient(
            connection_params=ConnectionParams.from_params(
                http_host=self.host,
                http_port=self.http_port,
                http_secure=False,
                grpc_host=self.host,
                grpc_port=self.grpc_port,
                grpc_secure=False,
            ),
            auth_client_secret=Auth.api_key(api_key),
        )
        await self.client.connect()
        return self.client

    async def ensure_collection(self):
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if await self.client.collections.exists(self.collection_name):
            return

        await self.client.collections.create(
            name=self.collection_name,
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="title", data_type=DataType.TEXT),
                Property(name="summary", data_type=DataType.TEXT),
            ],
        )

    async def insert_object(self, uuid: str, vector: list[float], properties: dict):
        try:
            if self.client is None:
                raise RuntimeError("Client not connected.")

            collection = self.client.collections.get(self.collection_name)
            await collection.data.insert(
                uuid=uuid,
                vector=vector,
                properties=properties,
            )
        except WeaviateBaseError as e:
            raise RuntimeError(f"Weaviate insertion failed: {e}") from e

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None


# ----------------------------
# Singleton Management
# ----------------------------
_weaviate_client: Optional[WeaviateClient] = None

def init_weaviate_client(
    host: str, http_port: str, grpc_port: str, collection_name: str
) -> WeaviateClient:
    global _weaviate_client

    if _weaviate_client is None:
        _weaviate_client = WeaviateClient(
            host=host, 
            http_port=http_port, 
            grpc_port=grpc_port, 
            collection_name=collection_name
        )

    return _weaviate_client

def get_weaviate_client() -> WeaviateClient:
    if _weaviate_client is None:
        raise RuntimeError("Weaviate not initialized.")

    return _weaviate_client

async def close_weaviate_client():
    global _weaviate_client

    if _weaviate_client:
        await _weaviate_client.close()
        _weaviate_client = None
