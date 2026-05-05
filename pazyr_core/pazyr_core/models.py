from typing import Dict, List, Literal
from datetime import datetime
from pydantic import BaseModel

from .types import Website

class IngestorConfig(BaseModel):
    log_level: Literal["INFO", "DEBUG", "ERROR", "WARNING"]
    sources: Dict[str, Website]
    topics: List[str]
    consumer_queue_size: int
    worker_count: int
    storage_path: str
    download_retry_count: int
    download_timeout_seconds: int
    crawler_rate_limit_seconds: float

    # redis specific configuration
    redis_url: str
    scheduled_crawl_job_stream_name: str
    processing_stream_name: str
    
    # Arxiv-specific configuration
    arxiv_batch_size: int



class PostgresConfig(BaseModel):
    host: str
    port: int
    database: str
    user: str

class WeaviateConfig(BaseModel):
    host: str
    http_port: int
    grpc_port: int

class SQLQueryConfig(BaseModel):
    query: str

class QueryConfig(BaseModel):
    create_job_table: SQLQueryConfig
    insert_job_status: SQLQueryConfig


class KBConfig(BaseModel):
    log_level: Literal["INFO", "DEBUG", "ERROR", "WARNING"]

    completed_folder_path: str

    # redis specific config
    redis_url: str
    processing_stream_name: str

    # Weaviate
    weaviate: WeaviateConfig
    weaviate_collection_name: str

    # ollama specific config
    ollama_api_endpoint: str
    ollama_embedding_model: str

    # Postgres
    postgres: PostgresConfig

    jobs_table_name: str

    # psql queries
    queries: QueryConfig
