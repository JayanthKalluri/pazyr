# Root Makefile

.PHONY: help build-all run-all build-core build-discovery-engine run-discovery-engine

help:
	@echo Usage: make [target]
	@echo Targets:
	@echo   build-all                   - Build core and discovery-engine
	@echo   run-all                     - Run discovery-engine via Docker Compose
	@echo   build-core                  - Build core component
	@echo   build-discovery-engine      - Lint/test/build discovery-engine
	@echo   run-discovery-engine        - Run discovery-engine via Docker Compose
	@echo   shutdown-discovery-engine   - Shutdown discovery-engine via Docker Compose

# Aggregate targets
build-all: build-core build-discovery-engine
run-all: run-discovery-engine

# Component targets
build-core:
	$(MAKE) -C pazyr_core build-core

ci-discovery-engine: 
	$(MAKE) -C services/discovery_engine ci

build-discovery-engine:
	podman compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml build pazyr_discovery_engine

run-discovery-engine:
	podman compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml up -d pazyr_discovery_engine

shutdown-discovery-engine:
	podman compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml down -v pazyr_discovery_engine