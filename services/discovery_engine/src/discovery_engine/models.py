from pazyr_core.settings import LoggingConfig, RedisConfig
from pazyr_core.types import Website
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class _WorkerConfig(BaseModel):
    count: int = Field(gt=0)
    queue_size: int = Field(gt=0)


class _StorageConfig(BaseModel):
    path: str


class _DownloadConfig(BaseModel):
    retry_count: int = Field(ge=0)
    timeout_seconds: int = Field(gt=0)


class _CrawlerConfig(BaseModel):
    rate_limit_seconds: float = Field(gt=0)


class _RedisStreamsConfig(BaseModel):
    scheduled_crawl_job: str
    processing: str


class _ArxivConfig(BaseModel):
    batch_size: int = Field(gt=0)


class DiscoveryEngineConfig(BaseSettings):
    service_name: str = "discovery-engine"

    logging: LoggingConfig

    sources: dict[str, Website]
    topics: list[str]

    workers: _WorkerConfig
    crawler: _CrawlerConfig

    redis: RedisConfig
    streams: _RedisStreamsConfig

    arxiv: _ArxivConfig