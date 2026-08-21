from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        extra="ignore",
    )
    
    host: str
    port: int = 5432
    database: str
    username: str
    password: SecretStr

    @property
    def connection_string(self) -> str:
        if not self.username:
            raise RuntimeError("Required env variable POSTGRES_USERNAME is not set, set and try again.")
        if not self.password:
            raise RuntimeError("Required env variable POSTGRES_PASSWORD is not set, set and try again.")
        if not self.database:
            raise RuntimeError("Required env variable POSTGRES_DATABASE is not set, set and try again.")

        return f"postgresql://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.database}"

class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str
    port: int = 6379
    database: int = 0
    username: str
    password: SecretStr

    @property
    def url(self) -> str:
        if not self.username:
            raise RuntimeError("Required env variable REDIS_USERNAME is not set, set and try again.")
        if not self.password:
            raise RuntimeError("Required env variable REDIS_PASSWORD is not set, set and try again.")

        return f"redis://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}" 
