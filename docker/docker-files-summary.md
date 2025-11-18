# Docker Files Reference

Complete reference for all Docker-related files in this project.

## 📁 File Structure

```
zurg-monitor/
├── Dockerfile                  # Main Docker image definition
├── .dockerignore              # Files to exclude from build context
├── docker-compose.yml         # Docker Compose configuration
├── Makefile                   # Build automation commands
├── build-docker.sh            # Interactive build script
├── zurg-monitor.py            # Main application
├── zurg-monitor.conf          # Configuration template
├── DOCKER.md                  # Comprehensive Docker guide
├── DOCKER_QUICKSTART.md       # Quick start guide
├── config/                    # Configuration directory (created)
│   └── zurg-monitor.conf     # User configuration
└── logs/                      # Log directory (created)
    └── zurg-monitor.log      # Application logs
```

## 📄 File Descriptions

### Dockerfile

**Purpose**: Defines the Docker image

**Key Features**:
- Multi-stage build for optimal size
- Based on Python 3.11-slim
- Runs as non-root user (UID 1000)
- Health checks included
- Volume mounts for config and logs
- Environment variable support
- Automatic config creation on first run

**Usage**:
```bash
docker build -t zurg-monitor:latest .
```

### .dockerignore

**Purpose**: Excludes unnecessary files from Docker build context

**Excludes**:
- Git files (.git, .gitignore)
- Documentation files (*.md)
- Local configuration and logs
- Python cache files
- IDE files
- Build artifacts

**Benefit**: Smaller build context = faster builds

### docker-compose.yml

**Purpose**: Orchestrate container deployment

**Includes**:
- Default configuration service
- Testing profiles (run-once, dry-run)
- Fast monitoring profile
- Authentication example
- Network configuration
- Volume management
- Logging configuration

**Services Defined**:
1. `zurg-monitor` - Default continuous monitoring
2. `zurg-monitor-once` - Single check (profile: testing)
3. `zurg-monitor-dryrun` - Dry run mode (profile: testing)
4. `zurg-monitor-fast` - High frequency (profile: fast)
5. `zurg-monitor-auth` - With auth (profile: auth)

**Usage**:
```bash
docker-compose up -d                    # Default service
docker-compose --profile testing up     # Testing service
```

### Makefile

**Purpose**: Simplify common Docker operations

**Key Targets**:
- `make help` - Show all commands
- `make setup` - Create directories and config
- `make build` - Build image
- `make build-multi` - Multi-platform build
- `make run` - Start with docker-compose
- `make run-once` - Single test run
- `make run-dryrun` - Dry run mode
- `make logs` - View logs
- `make shell` - Access container shell
- `make stop` - Stop containers
- `make clean` - Remove everything
- `make test` - Quick test

**Variables**:
- `IMAGE_NAME` - Image name (default: zurg-monitor)
- `VERSION` - Version tag (default: 3.0.0)
- `REGISTRY` - Registry URL (optional)

**Usage**:
```bash
make build
make run
make logs
```

### build-docker.sh

**Purpose**: Interactive Docker build script

**Features**:
- Prerequisites check (Docker, files)
- Multiple build options:
  1. Single platform (current)
  2. Multi-platform (amd64, arm64, arm/v7)
  3. Build and push to registry
  4. Clean build (no cache)
  5. Docker Compose build
- Automatic testing option
- Detailed build information
- Next steps guidance

**Usage**:
```bash
bash build-docker.sh
# Follow interactive prompts
```

## 🔧 Configuration Priority

Configuration values are applied in this order (highest to lowest):

1. **Environment variables** (runtime)
2. **Config file** (`/config/zurg-monitor.conf`)
3. **Built-in defaults** (in Python script)

### Example Override Chain

```bash
# Config file
[zurg]
check_interval = 30

# Docker environment
environment:
  - CHECK_INTERVAL=60        # This overrides config file

# Result: 60 minutes
```

## 🌍 Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ZURG_URL` | string | `http://localhost:9999` | Zurg server URL |
| `ZURG_USERNAME` | string | (empty) | Auth username |
| `ZURG_PASSWORD` | string | (empty) | Auth password |
| `CHECK_INTERVAL` | int | `30` | Minutes between checks |
| `RATE_LIMIT` | int | `10` | Requests before backoff |
| `RUN_ONCE` | bool | `false` | Run once and exit |
| `DEBUG` | bool | `false` | Enable debug logging |
| `TRACE` | bool | `false` | Enable trace logging |
| `DRY_RUN` | bool | `false` | Dry run mode |
| `TZ` | string | `UTC` | Container timezone |

## 📦 Volume Mounts

### Configuration Volume

**Container Path**: `/config`  
**Purpose**: Store configuration file  
**Contents**: `zurg-monitor.conf`

**Example**:
```yaml
volumes:
  - ./config:/config
```

### Logs Volume

**Container Path**: `/logs`  
**Purpose**: Store log files  
**Contents**: `zurg-monitor.log` + rotated logs

**Example**:
```yaml
volumes:
  - ./logs:/logs
```

### Persistent Named Volumes

```yaml
volumes:
  config-data:
  log-data:

services:
  zurg-monitor:
    volumes:
      - config-data:/config
      - log-data:/logs
```

## 🌐 Network Configurations

### Default Bridge Network

```yaml
services:
  zurg-monitor:
    # Uses default bridge network
    environment:
      - ZURG_URL=http://host.docker.internal:9999
```

### Custom Network

```yaml
networks:
  zurg-network:
    name: zurg-network
    driver: bridge

services:
  zurg-monitor:
    networks:
      - zurg-network
```

### External Network

```yaml
networks:
  existing-network:
    external: true

services:
  zurg-monitor:
    networks:
      - existing-network
```

### Host Network

```yaml
services:
  zurg-monitor:
    network_mode: host
```

## 🏷️ Image Tags

**Version Tag**: `zurg-monitor:3.0.0`  
**Latest Tag**: `zurg-monitor:latest`

**Build with tags**:
```bash
docker build -t zurg-monitor:3.0.0 -t zurg-monitor:latest .
```

## 🎯 Docker Compose Profiles

### Default (No Profile)

```bash
docker-compose up -d
```

Starts continuous monitoring service.

### Testing Profile

```bash
docker-compose --profile testing up zurg-monitor-once
```

Services:
- `zurg-monitor-once` - Single check with debug
- `zurg-monitor-dryrun` - Dry run with debug

### Fast Profile

```bash
docker-compose --profile fast up -d
```

Service: `zurg-monitor-fast` - 10-minute intervals

### Auth Profile

```bash
docker-compose --profile auth up -d
```

Service: `zurg-monitor-auth` - With authentication

## 🔨 Build Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `BUILD_DATE` | Build timestamp | Current date/time |
| `VERSION` | Application version | `3.0.0` |
| `VCS_REF` | Git commit hash | Current commit |

**Usage**:
```bash
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VERSION=3.0.0 \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t zurg-monitor:latest .
```

## 🏃 Common Workflows

### Development Workflow

```bash
# 1. Make changes to code
nano zurg-monitor.py

# 2. Rebuild
make build-nocache

# 3. Test
make run-dryrun

# 4. Deploy
make run
```

### Production Deployment

```bash
# 1. Setup
make setup
nano config/zurg-monitor.conf

# 2. Build
make build

# 3. Test
make test

# 4. Deploy
make run

# 5. Monitor
make logs
```

### Multi-Platform Build

```bash
# 1. Build for all platforms
make build-multi

# 2. Push to registry
make push REGISTRY=ghcr.io/username/

# 3. Pull on target system
docker pull ghcr.io/username/zurg-monitor:latest
```

## 🔍 Debugging

### View Build Logs

```bash
docker build --progress=plain -t zurg-monitor:latest .
```

### Inspect Image

```bash
docker inspect zurg-monitor:latest
docker history zurg-monitor:latest
```

### Container Debug

```bash
# Get shell
docker exec -it zurg-monitor /bin/bash

# Check processes
docker top zurg-monitor

# View config
docker exec zurg-monitor cat /config/zurg-monitor.conf

# Test connectivity
docker exec zurg-monitor curl http://zurg:9999/stats
```

## 📊 Image Information

**Base Image**: `python:3.11-slim`  
**User**: `zurg` (UID 1000)  
**Working Directory**: `/app`  
**Entrypoint**: `/app/entrypoint.sh`  
**Health Check**: Every 5 minutes

**Approximate Size**: ~150MB (depending on platform)

## 🔐 Security Features

1. **Non-root user** - Runs as UID 1000
2. **Minimal base image** - Python slim variant
3. **No unnecessary packages** - Only essentials
4. **Read-only config** - Can mount config as read-only
5. **Secret support** - Docker secrets compatible
6. **Resource limits** - CPU/memory limits supported

## 📝 Labels

All images include OCI standard labels:
- `org.opencontainers.image.title`
- `org.opencontainers.image.description`
- `org.opencontainers.image.version`
- `org.opencontainers.image.created`
- `org.opencontainers.image.revision`
- `org.opencontainers.image.source`
- `org.opencontainers.image.licenses`

## 🚀 Quick Reference

### Build Commands

```bash
make build              # Standard build
make build-multi        # Multi-platform
make build-nocache      # Clean build
bash build-docker.sh    # Interactive
docker-compose build    # With compose
```

### Run Commands

```bash
make run                # Start continuous
make run-once           # Single check
make run-dryrun         # Dry run
docker-compose up -d    # Start service
```

### Management Commands

```bash
make logs               # View logs
make shell              # Container shell
make stop               # Stop
make restart            # Restart
make clean              # Remove all
```

## 📚 Documentation Files

- **DOCKER.md** - Comprehensive Docker guide (full documentation)
- **DOCKER_QUICKSTART.md** - Quick start guide (get running fast)
- **DOCKER_FILES.md** - This file (reference for all files)
- **README.md** - Main project documentation
- **QUICK_REFERENCE.md** - Command reference

## 💡 Tips

1. Use `make help` for quick command reference
2. Always run `make setup` first
3. Test with `make run-dryrun` before production
4. Use `make logs` to monitor operation
5. Keep config in version control (without passwords)
6. Use environment variables for sensitive data
7. Regular image updates: `make build-nocache`
8. Monitor resource usage: `docker stats`

## ✅ Pre-deployment Checklist

- [ ] All files present (use `make check-files`)
- [ ] Configuration created (use `make setup`)
- [ ] Config edited with correct values
- [ ] Image built successfully (use `make build`)
- [ ] Tested with dry run (use `make run-dryrun`)
- [ ] Logs directory has write permissions
- [ ] Network connectivity verified
- [ ] Resource limits set (if needed)
- [ ] Restart policy configured
- [ ] Monitoring configured

---

**For detailed instructions, see [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)**