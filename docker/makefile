# ============================================================================
# Zurg Monitor - Makefile
# ============================================================================
# Quick commands for building and managing the Docker container
# ============================================================================

# Variables
IMAGE_NAME := zurg-monitor
VERSION := 3.0.0
REGISTRY := 
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
FULL_IMAGE := $(REGISTRY)$(IMAGE_NAME)

# Detect platform
PLATFORM := $(shell uname -m)
ifeq ($(PLATFORM),x86_64)
	DOCKER_PLATFORM := linux/amd64
else ifeq ($(PLATFORM),aarch64)
	DOCKER_PLATFORM := linux/arm64
else ifeq ($(PLATFORM),armv7l)
	DOCKER_PLATFORM := linux/arm/v7
else
	DOCKER_PLATFORM := linux/amd64
endif

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

.PHONY: help build build-multi build-nocache build-compose push test run run-once run-dryrun stop restart logs shell clean prune setup check-files

# Default target
.DEFAULT_GOAL := help

## help: Show this help message
help:
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║          Zurg Monitor - Docker Makefile Commands                    ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Build Commands:$(NC)"
	@grep -E '^## build' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'
	@echo ""
	@echo "$(GREEN)Run Commands:$(NC)"
	@grep -E '^## run' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'
	@echo ""
	@echo "$(GREEN)Management Commands:$(NC)"
	@grep -E '^## (stop|restart|logs|shell|clean|prune)' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@grep -E '^## (setup|check-files|test|push)' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make build           # Build Docker image"
	@echo "  make run            # Run container with docker-compose"
	@echo "  make logs           # View container logs"
	@echo "  make shell          # Get a shell in the container"
	@echo ""

## check-files: Check if all required files exist
check-files:
	@echo "$(CYAN)Checking required files...$(NC)"
	@test -f Dockerfile || (echo "$(RED)✗ Dockerfile not found$(NC)" && exit 1)
	@test -f zurg-monitor.py || (echo "$(RED)✗ zurg-monitor.py not found$(NC)" && exit 1)
	@test -f zurg-monitor.conf || (echo "$(RED)✗ zurg-monitor.conf not found$(NC)" && exit 1)
	@test -f .dockerignore || (echo "$(RED)✗ .dockerignore not found$(NC)" && exit 1)
	@test -f docker-compose.yml || (echo "$(RED)✗ docker-compose.yml not found$(NC)" && exit 1)
	@echo "$(GREEN)✓ All required files present$(NC)"

## setup: Create necessary directories and config
setup:
	@echo "$(CYAN)Setting up directories...$(NC)"
	@mkdir -p config logs
	@if [ ! -f config/zurg-monitor.conf ]; then \
		echo "$(CYAN)Creating default configuration...$(NC)"; \
		cp zurg-monitor.conf config/; \
		echo "$(GREEN)✓ Configuration created$(NC)"; \
		echo "$(YELLOW)⚠ Please edit config/zurg-monitor.conf$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Config already exists, skipping$(NC)"; \
	fi
	@echo "$(GREEN)✓ Setup complete$(NC)"

## build: Build Docker image for current platform
build: check-files
	@echo "$(CYAN)Building Docker image...$(NC)"
	docker build \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		--build-arg VCS_REF=$(VCS_REF) \
		-t $(FULL_IMAGE):$(VERSION) \
		-t $(FULL_IMAGE):latest \
		.
	@echo "$(GREEN)✓ Build complete$(NC)"

## build-multi: Build Docker image for multiple platforms (amd64, arm64, arm/v7)
build-multi: check-files
	@echo "$(CYAN)Building multi-platform Docker image...$(NC)"
	@docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch
	docker buildx build \
		--platform linux/amd64,linux/arm64,linux/arm/v7 \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		--build-arg VCS_REF=$(VCS_REF) \
		-t $(FULL_IMAGE):$(VERSION) \
		-t $(FULL_IMAGE):latest \
		--load \
		.
	@echo "$(GREEN)✓ Multi-platform build complete$(NC)"

## build-nocache: Build Docker image without cache (clean build)
build-nocache: check-files
	@echo "$(CYAN)Building Docker image (no cache)...$(NC)"
	docker build --no-cache \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		--build-arg VCS_REF=$(VCS_REF) \
		-t $(FULL_IMAGE):$(VERSION) \
		-t $(FULL_IMAGE):latest \
		.
	@echo "$(GREEN)✓ Build complete$(NC)"

## build-compose: Build using docker-compose
build-compose: check-files
	@echo "$(CYAN)Building with docker-compose...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

## push: Push image to registry
push: build-multi
	@echo "$(CYAN)Pushing to registry...$(NC)"
	@if [ -z "$(REGISTRY)" ]; then \
		echo "$(RED)✗ REGISTRY variable not set$(NC)"; \
		echo "$(YELLOW)Usage: make push REGISTRY=ghcr.io/username/$(NC)"; \
		exit 1; \
	fi
	docker buildx build \
		--platform linux/amd64,linux/arm64,linux/arm/v7 \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		--build-arg VCS_REF=$(VCS_REF) \
		-t $(FULL_IMAGE):$(VERSION) \
		-t $(FULL_IMAGE):latest \
		--push \
		.
	@echo "$(GREEN)✓ Push complete$(NC)"

## test: Run a quick test of the image
test: build
	@echo "$(CYAN)Running test...$(NC)"
	@mkdir -p test-config test-logs
	@cp zurg-monitor.conf test-config/
	docker run --rm \
		-v $(PWD)/test-config:/config \
		-v $(PWD)/test-logs:/logs \
		-e ZURG_URL=http://host.docker.internal:9999 \
		-e RUN_ONCE=true \
		-e DEBUG=true \
		$(FULL_IMAGE):latest || true
	@rm -rf test-config test-logs
	@echo "$(GREEN)✓ Test complete$(NC)"

## run: Start container with docker-compose
run: setup
	@echo "$(CYAN)Starting container with docker-compose...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Container started$(NC)"
	@echo "$(YELLOW)View logs with: make logs$(NC)"

## run-once: Run container once for testing
run-once: setup
	@echo "$(CYAN)Running container once...$(NC)"
	docker run --rm \
		-v $(PWD)/config:/config \
		-v $(PWD)/logs:/logs \
		-e RUN_ONCE=true \
		-e DEBUG=true \
		$(FULL_IMAGE):latest

## run-dryrun: Run in dry-run mode (no repairs triggered)
run-dryrun: setup
	@echo "$(CYAN)Running in dry-run mode...$(NC)"
	docker run --rm \
		-v $(PWD)/config:/config \
		-v $(PWD)/logs:/logs \
		-e RUN_ONCE=true \
		-e DRY_RUN=true \
		-e DEBUG=true \
		$(FULL_IMAGE):latest

## stop: Stop running containers
stop:
	@echo "$(CYAN)Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

## restart: Restart containers
restart:
	@echo "$(CYAN)Restarting containers...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Containers restarted$(NC)"

## logs: View container logs
logs:
	@echo "$(CYAN)Viewing logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f zurg-monitor

## shell: Get a shell in the running container
shell:
	@echo "$(CYAN)Opening shell in container...$(NC)"
	docker exec -it zurg-monitor /bin/bash || docker exec -it zurg-monitor /bin/sh

## clean: Remove containers and volumes
clean:
	@echo "$(CYAN)Cleaning up containers and volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## prune: Remove all unused Docker resources
prune:
	@echo "$(CYAN)Pruning Docker resources...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Prune complete$(NC)"

# Info target (hidden)
info:
	@echo "$(CYAN)Build Information:$(NC)"
	@echo "  Image:      $(FULL_IMAGE)"
	@echo "  Version:    $(VERSION)"
	@echo "  Platform:   $(DOCKER_PLATFORM)"
	@echo "  Build Date: $(BUILD_DATE)"
	@echo "  VCS Ref:    $(VCS_REF)"

# Quick aliases
up: run
down: stop
rebuild: build-nocache run