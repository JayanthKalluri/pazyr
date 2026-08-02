# TODO - pazyr_core Architecture Review

## Overall Verdict

Current Rating: **7.5 / 10**

The package already has a solid foundation:

- ✅ Clean project structure
- ✅ Async-first design
- ✅ Typed configuration using Pydantic
- ✅ Reusable infrastructure clients
- ✅ Public package API through `__init__.py`

However, the package currently mixes **infrastructure concerns** with **application-specific concerns**, which will become a maintenance burden as more teams adopt it.

The long-term goal should be:

> **pazyr_core should be an infrastructure SDK, not an application SDK.**

---

# P0 (Must Fix Before Wider Adoption)

## 1. Remove application-specific models

### Current

```
types.py

Website
Artifact
JobObject
ScheduledCrawlJob
```

These belong to the Ingestor/Knowledge Base applications, not to the shared infrastructure package.

### Goal

Move them into:

```
pazyr_models
```

or

```
ingestor_models
```

The core package should only expose generic infrastructure models.

---

## 2. Remove application-specific configs

Current:

```
IngestorConfig
KBConfig
```

These are service-specific.

Instead expose reusable configs:

```
RedisConfig
PostgresConfig
WeaviateConfig
LoggerConfig
```

Applications should compose them.

Example:

```python
class IngestorConfig(BaseModel):
    redis: RedisConfig
    postgres: PostgresConfig
    logger: LoggerConfig
```

---

## 3. Remove application constants

Current constants:

```
DOWNLOADER_STREAM_NAME
CRAWLER_CONSUMER
JOBS_TABLE_NAME
```

These should not live inside a shared infrastructure package.

Infrastructure packages should only provide generic defaults like:

```
DEFAULT_TIMEOUT
DEFAULT_STREAM_LENGTH
DEFAULT_POOL_SIZE
```

---

## 4. Stop reading environment variables inside library code

Current:

```python
os.getenv(...)
```

Libraries should never decide where configuration comes from.

Instead:

```python
WeaviateConfig(
    api_key=...
)
```

Inject configuration from the application.

---

## 5. Introduce custom exceptions

Replace generic

```
RuntimeError
```

with package-specific exceptions.

Example:

```
CoreError

ConfigurationError

InitializationError

ConnectionError

DatabaseError

VectorStoreError
```

This gives downstream services much better error handling.

---

# P1 (High Priority)

## 6. Introduce a unified lifecycle

Current:

```
init_redis()

init_postgres()

init_weaviate()

shutdown...
```

Instead expose:

```python
await pazyr.initialize(config)

redis = pazyr.redis()

postgres = pazyr.postgres()

weaviate = pazyr.weaviate()

await pazyr.shutdown()
```

One entry point.

One shutdown.

One lifecycle.

---

## 7. Remove duplicated singleton registry logic

Current:

Every client implements

```
_clients = {}

_lock = Lock()

init()

get()

close()
```

Create one reusable registry instead.

Example:

```
ClientRegistry
```

or

```
SingletonRegistry[T]
```

Every infrastructure component should use the same registry.

---

## 8. Avoid exposing implementation details

Instead of exposing

```
RedisClient
PostgresClient
WeaviateClient
```

consider exposing abstractions.

Examples:

```
Queue

Database

VectorStore
```

Internally they can still use Redis/Postgres/Weaviate.

This reduces coupling.

---

## 9. Don't configure the root logger

Current logger config modifies the global root logger.

Instead configure only

```
logging.getLogger("pazyr")
```

This avoids affecting applications that use the package.

---

## 10. Add async context manager support

Support

```python
async with PostgresClient(...) as db:
    ...
```

instead of requiring manual connect/close.

Same for Redis and Weaviate where applicable.

---

## 11. Improve transaction API

Current:

```python
conn, tx = await transaction()
```

Consumers are responsible for

- commit
- rollback
- release

Prefer

```python
async with postgres.transaction() as conn:
    ...
```

The package should manage lifecycle automatically.

---

# P2 (Medium Priority)

## 12. Reorganize package layout

Suggested structure

```
pazyr_core/

    clients/

    config/

    exceptions/

    logging/

    registry/

    interfaces/

    lifecycle/

    utils/
```

Keep application/domain models outside this package.

---

## 13. Improve typing

Use stronger type hints where possible.

Examples:

- Mapping instead of Dict
- Sequence instead of List
- Typed aliases for IDs
- Generic registry types

---

## 14. Improve documentation

Every public API should include

- purpose
- arguments
- return value
- exceptions
- usage example

Generate documentation from docstrings.

---

## 15. Publish API guidelines

Define which APIs are considered stable.

Anything exported from

```
pazyr_core.__init__
```

should be treated as public.

Everything else should be considered internal.

---

# P3 (Nice Improvements)

## 16. Add retry policies

Support configurable retries for

- Redis
- Postgres
- Weaviate

using exponential backoff.

---

## 17. Metrics hooks

Allow applications to register metrics.

Examples:

- query latency
- queue latency
- retries
- failures

---

## 18. Tracing support

Add optional OpenTelemetry integration.

---

## 19. Health checks

Every infrastructure client should expose

```python
await client.health()
```

---

## 20. Structured logging

Support structured JSON logging in addition to console output.

---

## 21. Better packaging

Add

- LICENSE
- CHANGELOG.md
- CONTRIBUTING.md
- API compatibility policy

---

## 22. Testing

Target near-100% coverage.

Recommended layout:

```
tests/

    test_logger.py

    test_registry.py

    test_postgres.py

    test_redis.py

    test_weaviate.py

    test_config.py
```

Infrastructure packages should be the most thoroughly tested code in the organization.

---

# Release Checklist

Before v1.0.0:

- [ ] Remove application-specific models
- [ ] Remove application-specific configuration
- [ ] Remove application-specific constants
- [ ] Introduce custom exception hierarchy
- [ ] Introduce shared client registry
- [ ] Implement unified initialization/shutdown
- [ ] Add async context managers
- [ ] Add transaction context manager
- [ ] Avoid root logger configuration
- [ ] Remove environment variable access from library
- [ ] Write comprehensive tests
- [ ] Add API documentation
- [ ] Add CHANGELOG
- [ ] Define semantic versioning policy

---

# Final Verdict

This repository is already a **good engineering foundation**, but it is currently positioned halfway between a **shared infrastructure SDK** and an **application-common library**.

The biggest architectural improvement is to **separate infrastructure from business/domain concerns**. Once that boundary is enforced, `pazyr_core` can become a stable internal SDK that multiple teams can depend on confidently with minimal coupling.

**Target Rating after completing this TODO:** **9.5+/10**