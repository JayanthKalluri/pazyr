# Root Makefile

ifeq ($(OS),Windows_NT)
    UNAME_S := Windows
    CONTAINER_RUNTIME := $(if $(shell where podman 2>nul),podman,$(if $(shell where docker 2>nul),docker,))
else
    UNAME_S := $(shell uname -s)
    CONTAINER_RUNTIME := $(shell command -v podman || command -v docker)
endif

ifeq ($(CONTAINER_RUNTIME),)
$(error No container runtime found (install Docker or Podman))
endif

.PHONY: help prerequisites build-all run-all build-core ci-core ci-discovery-engine build-discovery-engine run-discovery-engine shutdown-discovery-engine

help:
	@echo Usage: make [target]
	@echo Targets:
	@echo   build-all                   - Build core and discovery-engine
	@echo   run-all                     - Run discovery-engine via Compose
	@echo   build-core                  - Build core component
	@echo   ci-core                       - Run core component tests
	@echo   ci-discovery-engine         - Run discovery-engine tests
	@echo   build-discovery-engine      - Lint/test/build discovery-engine
	@echo   run-discovery-engine        - Run discovery-engine via Compose
	@echo   shutdown-discovery-engine   - Shutdown discovery-engine via Compose


# ---------------------------
# Aggregate targets
# ---------------------------
build-all: build-core build-discovery-engine
run-all: prerequisites run-discovery-engine

# ---------------------------
# Component targets
# ---------------------------
ci-core:
	$(MAKE) -C pazyr_core ci

build-core:
	ci-core
	$(MAKE) -C pazyr_core build-core

# ---------------------------
# Prerequisites for all services
# ---------------------------
prerequisites:
ifeq ($(OS),Windows_NT)
	powershell.exe -ExecutionPolicy Bypass -File scripts/create_docker_network.ps1
else ifeq ($(UNAME_S),Linux)
	bash scripts/create_docker_network.sh
else
	@echo "Unsupported OS: $(UNAME_S)"
endif

# ---------------------------
# Component-specific targets
# ---------------------------

# Discovery Engine
ci-discovery-engine:
	$(MAKE) -C services/discovery_engine ci


build-discovery-engine:
	ci-discovery-engine
	$(CONTAINER_RUNTIME) compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml --profile v1-uat build pazyr_discovery_engine

# Ensure prerequisites runs before run-discovery-engine
run-discovery-engine: 
	prerequisites
	$(CONTAINER_RUNTIME) compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml --profile v1-uat up -d pazyr_discovery_engine

shutdown-discovery-engine:
	$(CONTAINER_RUNTIME) compose -f ./docker-compose.yaml -f ./docker-compose.dev.yaml --profile v1-uat down -v pazyr_discovery_engine


# Analysing Engine