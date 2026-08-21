from pazyr_core.settings import LoggingConfig, RedisConfig, PostgresConfig
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


# class _StorageLocation(BaseModel):
#     type: Literal["local"]
#     path: str | None = None
#     bucket: str | None = None
#     prefix: str | None = None
#     container: str | None = None

# class _StorageConfig(BaseModel):
#     completed: _StorageLocation | None = None
#     failed: _StorageLocation | None = None

class _ModelConfig(BaseModel):
    provider: str
    model: str
    endpoint: str
    api_key: SecretStr

class _AiConfig(BaseModel):
    llm: _ModelConfig
    embeddings: _ModelConfig


class AnalysingEngineConfig(BaseSettings):
    service_name: str = "analysing-engine"

    logging: LoggingConfig

    # storage: _StorageConfig

    redis: RedisConfig

    database: PostgresConfig

    ai: _AiConfig