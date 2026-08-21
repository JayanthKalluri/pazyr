# Pazyr

Pazyr is a microservice-based pipeline for discovering scientific documents, downloading PDFs, and building an embedded knowledge layer.

The repository includes:

- `pazyr_core/` — shared infrastructure utilities, clients, and typed settings.
- `services/discovery_engine/` — discovery crawler that scrapes sources, downloads PDFs, and publishes jobs to Redis.
- `services/knowledge_builder/` — worker that consumes Redis jobs, embeds content, and stores vectors in Weaviate.
- `config/` — YAML service configurations.
- `infra/` — Docker environment configuration for Redis, Postgres, and Weaviate.

## Architecture

1. `discovery_engine` crawls sources such as arXiv and creates PDF ingestion jobs.
2. Jobs are published to Redis streams.
3. `knowledge_builder` consumes jobs, extracts metadata, generates embeddings, and inserts data into Weaviate.
4. PostgreSQL is used for supplemental job tracking and state.

## Directory layout

- `docker-compose.yaml` — production compose file for services and infra.
- `docker-compose.dev.yaml` — development compose file with profiles.
- `packages/pazyr_core-0.1.0-py3-none-any.whl` — local wheel used by discovery engine.
- `pazyr_core/` — shared package sources.
- `services/discovery_engine/` — discovery engine service.
- `services/knowledge_builder/` — knowledge builder service.
- `config/` — service YAML configuration files.
- `infra/` — Redis, Postgres, and Weaviate config.

## Requirements

- Docker
- Docker Compose
- Python 3.12+ (for local development)

## Quick start

1. Ensure the Docker network exists:

```bash
docker network create pazyr_network
```

2. Start infrastructure and services:

```bash
docker compose up -d
```

3. Check logs:

```bash
docker compose logs -f pazyr_discovery_engine

docker compose logs -f pazyr_knowledge_builder
```

## Configuration

Configuration is driven by YAML files mounted into containers:

- `config/discovery_engine.yaml`
- `config/knowledge_builder.yaml`

The services expect these environment variables:

- `CONFIG_FILEPATH` — path to the YAML config file.
- `POSTGRES_PASSWORD` — required by `knowledge_builder` when connecting to Postgres.

### Example config values

`config/discovery_engine.yaml` includes:

- `service_name`
- `sources`
- `topics`
- `workers.count`
- `crawler.rate_limit_seconds`
- `redis.host` / `redis.port`
- `streams.scheduled_crawl_job`
- `streams.processing`
- `arxiv.batch_size`

`config/knowledge_builder.yaml` includes:

- `completed_folder_path`
- `redis_url`
- `processing_stream_name`
- `weaviate.host`
- `weaviate.http_port`
- `weaviate.grpc_port`
- `ollama_api_endpoint`
- `ollama_embedding_model`
- `postgres` connection settings
- SQL query templates for job tracking

## Running locally

### Discovery Engine

```bash
cd services/discovery_engine
uv sync --frozen --no-dev
uv run discovery-engine
```

This service loads `CONFIG_FILEPATH` from the environment and uses the local `pazyr_core` wheel package.

### Knowledge Builder

```bash
cd services/knowledge_builder
pip install -e .
python -m knowledge_builder.main
```

This service also respects `CONFIG_FILEPATH` and loads `POSTGRES_PASSWORD` from the environment.

## Docker service details

### Discovery Engine

- Dockerfile installs Python dependencies via `uv`.
- It loads the YAML config from `CONFIG_FILEPATH`.
- It creates Redis consumer groups and starts crawler workers.

### Knowledge Builder

- Dockerfile installs `pazyr_core` and the knowledge builder package in editable mode.
- It connects to Redis, Weaviate, and Postgres.
- It uses Ollama embeddings to vectorize processed text.

## Notes

- `infra/redis/redis.conf` configures Redis.
- `infra/postgres/postgres.env` configures Postgres credentials.
- `infra/weaviate/weaviate.env` configures Weaviate.
- `volumes/data/` is used for shared document storage.

## Next steps

- Add a `README.md` to `services/knowledge_builder/` to describe worker-specific behavior.
- Add automated tests and health checks for each service.
- Document the Redis stream schema and job payload format.
