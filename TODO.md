# Production Readiness TODO

This repository is currently functional in a development context, but several improvements are needed to move it into production.

## Testing and Validation
- Add automated unit tests for all service modules, including `discovery_engine/main.py`, `crawler/manager.py`, and downloader flows.
- Add integration tests for Redis stream publishing/consuming and end-to-end discovery flow.
- Add contract tests for config loading and schema validation.
- Measure and enforce line coverage with a threshold (e.g. 80% or higher).
- Add test runners and CI integration for `pytest` and coverage reporting.
- Add health-check tests for Redis and Postgres connectivity.

## Code Quality and Design
- Remove stale or unused code in `services/discovery_engine/downloader/worker.py` or refactor it to align with current client APIs.
- Separate application-specific models from `pazyr_core`; move `Artifact`, `JobObject`, `Website`, and service-specific types into service packages.
- Clean up commented-out legacy code in `pazyr_core/clients/postgres_client.py` and `pazyr_core/clients/redis_client.py`.
- Replace generic `RuntimeError` usage with custom exceptions for better error handling.
- Ensure consistent naming for client APIs and returned objects.
- Avoid importing and validating config at module import time; use explicit initialization instead.
- Make Redis stream payload schemas explicit and document field structure.
- Reduce broad exception handlers and add explicit retry/dead-letter logic.
- Normalize date/time types consistently across `Artifact`, `JobObject`, and crawler parsing.

## Configuration and Deployment
- Standardize configuration across services; avoid mismatch between YAML fields and `pydantic` models.
- Add service-specific README and config documentation for `services/discovery_engine`.
- Document required environment variables clearly and load them safely in the application startup path.
- Add support for secure secrets management rather than hard-coded or local YAML secrets.

## Docker and Infrastructure
- Add container health checks for Redis, Postgres, and service containers.
- Ensure `docker-compose.yaml` and `docker-compose.dev.yaml` are consistent and include proper service dependency ordering.
- Add logs and metrics collection hooks for production observability.
- Validate volume mounts and network configuration for production usage.
- Add a production-ready Docker build/test workflow and CI pipeline.

## Security and Reliability
- Add secure defaults for Redis and Postgres credentials; avoid using default credentials in production.
- Validate and sanitize all external inputs from Redis streams and HTTP sources.
- Add logging that avoids sensitive information and supports structured error reporting.
- Add retry/backoff and circuit breaker patterns for external dependencies.
- Add documentation for security posture and operational readiness.

## Documentation
- Add a root `README.md` section for production deployment guidance.
- Add a `TODO.md` or upgrade checklist for future maintainers that covers architecture, tests, and release process.
- Document Redis stream schema, job payload formats, and service startup steps.
- Add changelog or versioning guidance if this project moves to production.

## Notes
- The current repository already has a good async design and shared client infrastructure, but production readiness requires stronger separation of concerns, test coverage, config validation, and deployment hardening.
