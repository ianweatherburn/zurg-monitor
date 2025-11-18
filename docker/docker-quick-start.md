# Docker Quick Start Guide

Get Zurg Monitor running in Docker in under 5 minutes!

## ⚡ Super Quick Start (TL;DR)

```bash
# 1. Clone/download files
git clone <repo-url> && cd zurg-monitor

# 2. Setup directories and config
make setup

# 3. Edit configuration
nano config/zurg-monitor.conf

# 4. Build and run
make build run

# 5. Check logs
make logs
```

## 📦 What You Need

- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker)
- The project files (Dockerfile, docker-compose.yml, etc.)

## 🚀 Method 1: Using Makefile (Easiest)

### Step 1: Setup

```bash
make setup
```

This creates `config/` and `logs/` directories and copies the default configuration.

### Step 2: Configure

Edit `config/zurg-monitor.conf`:

```bash
nano config/zurg-monitor.conf
```

Change these settings:
```ini
[zurg]
zurg_url = http://zurg:9999  # Or your Zurg URL
username = riven              # If authentication needed
password = 12345              # If authentication needed
```

### Step 3: Build

```bash
make build
```

### Step 4: Run

```bash
make run
```

### Step 5: Check Status

```bash
make logs
```

### Common Makefile Commands

```bash
make help          # Show all commands
make build         # Build image
make run           # Start container
make stop          # Stop container
make restart       # Restart container
make logs          # View logs
make shell         # Get shell access
make run-once      # Test run
make run-dryrun    # Dry run (no repairs)
make clean         # Remove containers
```

## 🔧 Method 2: Using docker-compose

### Step 1: Create Directories

```bash
mkdir -p config logs
```

### Step 2: Create Configuration

```bash
cp zurg-monitor.conf config/
nano config/zurg-monitor.conf
```

### Step 3: Build

```bash
docker-compose build
```

### Step 4: Start

```bash
docker-compose up -d
```

### Step 5: Check Logs

```bash
docker-compose logs -f zurg-monitor
```

### Common docker-compose Commands

```bash
docker-compose up -d              # Start in background
docker-compose up                 # Start with logs
docker-compose down               # Stop and remove
docker-compose restart            # Restart
docker-compose logs -f            # Follow logs
docker-compose ps                 # Show status
docker-compose pull               # Pull latest image
docker-compose build --no-cache   # Rebuild from scratch
```

## 🐳 Method 3: Using Docker Directly

### Step 1: Build Image

```bash
docker build -t zurg-monitor:latest .
```

### Step 2: Create Directories

```bash
mkdir -p config logs
cp zurg-monitor.conf config/
```

### Step 3: Edit Configuration

```bash
nano config/zurg-monitor.conf
```

### Step 4: Run Container

```bash
docker run -d \
  --name zurg-monitor \
  --restart unless-stopped \
  -v $(pwd)/config:/config \
  -v $(pwd)/logs:/logs \
  -e ZURG_URL=http://zurg:9999 \
  zurg-monitor:latest
```

### Step 5: Check Status

```bash
docker logs -f zurg-monitor
```

### Common Docker Commands

```bash
docker ps                         # List running containers
docker ps -a                      # List all containers
docker logs -f zurg-monitor       # Follow logs
docker stop zurg-monitor          # Stop container
docker start zurg-monitor         # Start container
docker restart zurg-monitor       # Restart container
docker rm zurg-monitor            # Remove container
docker exec -it zurg-monitor bash # Get shell
```

## 🎯 Quick Testing

### Test Build

```bash
make test
# OR
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/logs:/logs \
  -e ZURG_URL=http://zurg:9999 \
  -e RUN_ONCE=true \
  -e DEBUG=true \
  zurg-monitor:latest
```

### Dry Run (No Repairs)

```bash
make run-dryrun
# OR
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/logs:/logs \
  -e ZURG_URL=http://zurg:9999 \
  -e RUN_ONCE=true \
  -e DRY_RUN=true \
  -e DEBUG=true \
  zurg-monitor:latest
```

## 📝 Configuration Examples

### Example 1: Basic Setup

**config/zurg-monitor.conf:**
```ini
[zurg]
zurg_url = http://zurg:9999
check_interval = 30
log_file = /logs/zurg-monitor.log
```

**docker-compose.yml:**
```yaml
services:
  zurg-monitor:
    image: zurg-monitor:latest
    volumes:
      - ./config:/config
      - ./logs:/logs
    environment:
      - ZURG_URL=http://zurg:9999
```

### Example 2: With Authentication

**config/zurg-monitor.conf:**
```ini
[zurg]
zurg_url = http://zurg:9999
username = riven
password = 12345
check_interval = 30
```

### Example 3: High Frequency

**Environment variables in docker-compose.yml:**
```yaml
environment:
  - ZURG_URL=http://zurg:9999
  - CHECK_INTERVAL=10
  - RATE_LIMIT=20
  - DEBUG=true
```

### Example 4: External Zurg Server

**If Zurg is on another machine:**
```ini
[zurg]
zurg_url = http://192.168.1.100:9999
```

**If Zurg is on host machine:**
```ini
[zurg]
zurg_url = http://host.docker.internal:9999
```

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check container status
docker ps -a | grep zurg-monitor

# View logs
docker logs zurg-monitor

# Check configuration
docker exec zurg-monitor cat /config/zurg-monitor.conf
```

### Can't Connect to Zurg

```bash
# Test from container
docker exec zurg-monitor curl http://zurg:9999/stats

# Check if Zurg URL is correct
cat config/zurg-monitor.conf
```

### Permission Errors

```bash
# Fix permissions
sudo chown -R 1000:1000 config logs

# Or run as root
docker run --user root ...
```

### View Detailed Logs

```bash
# Enable debug mode
docker run -e DEBUG=true ...

# Enable trace mode (very verbose)
docker run -e TRACE=true ...
```

### Rebuild Everything

```bash
# Stop and remove
docker-compose down -v

# Remove image
docker rmi zurg-monitor:latest

# Rebuild
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

## 🌐 Network Scenarios

### Scenario 1: Zurg in Same Compose

```yaml
services:
  zurg:
    image: ghcr.io/debridmediamanager/zurg-testing:latest
    ports:
      - "9999:9999"

  zurg-monitor:
    image: zurg-monitor:latest
    environment:
      - ZURG_URL=http://zurg:9999
```

### Scenario 2: Zurg in External Network

```yaml
services:
  zurg-monitor:
    image: zurg-monitor:latest
    networks:
      - external_network

networks:
  external_network:
    external: true
    name: zurg_network
```

### Scenario 3: Zurg on Host

```yaml
services:
  zurg-monitor:
    image: zurg-monitor:latest
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - ZURG_URL=http://host.docker.internal:9999
```

## 🎓 Advanced Usage

### Using Docker Profiles

```bash
# Run with testing profile
docker-compose --profile testing up zurg-monitor-once

# Run with fast profile
docker-compose --profile fast up -d zurg-monitor-fast

# Run with auth profile
docker-compose --profile auth up -d zurg-monitor-auth
```

### Resource Limits

Add to docker-compose.yml:
```yaml
services:
  zurg-monitor:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

### Custom Logging

```yaml
services:
  zurg-monitor:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

### Health Checks

```yaml
services:
  zurg-monitor:
    healthcheck:
      test: ["CMD", "python3", "-c", "import sys; sys.exit(0)"]
      interval: 5m
      timeout: 30s
      retries: 3
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
docker logs -f zurg-monitor

# Last 100 lines
docker logs --tail=100 zurg-monitor

# Since 1 hour ago
docker logs --since 1h zurg-monitor
```

### Container Stats

```bash
# Resource usage
docker stats zurg-monitor

# Detailed info
docker inspect zurg-monitor
```

### Log Files

```bash
# View log file
tail -f logs/zurg-monitor.log

# Search logs
grep "ERROR" logs/zurg-monitor.log
```

## 🔄 Updates

### Update Image

```bash
# Pull latest
git pull

# Rebuild
docker-compose build

# Restart
docker-compose up -d
```

### Update Config

```bash
# Edit config
nano config/zurg-monitor.conf

# Restart container
docker-compose restart
```

## 🛑 Stopping

### Temporary Stop

```bash
docker-compose stop
# OR
docker stop zurg-monitor
```

### Complete Removal

```bash
docker-compose down
# OR
docker stop zurg-monitor && docker rm zurg-monitor
```

### Remove Everything

```bash
# Remove containers, volumes, and images
docker-compose down -v --rmi all

# Remove directories
rm -rf config logs
```

## 💡 Tips

1. **Always test first**: Use `make run-once` or `--dry-run` before production
2. **Check logs regularly**: Use `make logs` or `docker logs -f`
3. **Keep config backed up**: Store `config/zurg-monitor.conf` safely
4. **Use environment variables**: For sensitive data instead of config file
5. **Monitor resource usage**: Use `docker stats` to check CPU/memory
6. **Update regularly**: Rebuild image for latest fixes
7. **Use named volumes**: For production deployments
8. **Set resource limits**: Prevent container from consuming too much

## 📚 Next Steps

- Read [DOCKER.md](DOCKER.md) for comprehensive documentation
- Check [README.md](README.md) for detailed features
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command reference

## 🆘 Getting Help

If something isn't working:

1. Check logs: `docker logs zurg-monitor`
2. Enable debug: `-e DEBUG=true`
3. Test connection: `docker exec zurg-monitor curl http://zurg:9999/stats`
4. Verify config: `docker exec zurg-monitor cat /config/zurg-monitor.conf`
5. Review this guide's troubleshooting section

## ✅ Checklist

Before running in production:

- [ ] Docker and Docker Compose installed
- [ ] All required files present
- [ ] Configuration file edited
- [ ] Zurg URL is correct
- [ ] Tested with `--dry-run`
- [ ] Logs are accessible
- [ ] Container restarts on failure
- [ ] Resource limits set (optional)
- [ ] Monitoring configured (optional)

---

**You're all set! 🎉**

Start monitoring with: `make run` or `docker-compose up -d`