# Environment Variables Setup Guide

Quick guide for setting up Zurg Monitor with environment variables and Docker.

## Quick Setup

```bash
# 1. Copy sample environment file
cp .env.sample .env

# 2. Find your user/group IDs
id -u  # This is your PUID
id -g  # This is your PGID

# 3. Edit .env file
nano .env

# 4. Start with docker-compose
docker-compose up -d
```

## Finding Your PUID and PGID

### On Linux/macOS:
```bash
# Get your user ID (PUID)
id -u
# Output: 1000

# Get your group ID (PGID)
id -g
# Output: 1000

# Get both at once
id
# Output: uid=1000(username) gid=1000(groupname) groups=...
```

### Why PUID/PGID Matter

When running in Docker, files created by the container need to have the correct permissions so you can access them from your host system. Setting PUID/PGID ensures:

- ✅ Log files are owned by your user
- ✅ Config files are accessible
- ✅ No permission denied errors
- ✅ Easy backup and maintenance

## Basic .env Configuration

### Minimum Required Settings

```bash
# .env
ZURG_URL=http://zurg:9999
PUID=1000
PGID=1000
```

### Recommended Settings

```bash
# .env
# Connection
ZURG_URL=http://zurg:9999
ZURG_USERNAME=riven
ZURG_PASSWORD=12345

# User/Group
PUID=1000
PGID=1000

# Monitoring
CHECK_INTERVAL=30
RATE_LIMIT=10

# Timezone
TZ=America/New_York
```

## .env File Structure

```bash
# ============================================================================
# CONNECTION SETTINGS
# ============================================================================
ZURG_URL=http://zurg:9999          # Where is Zurg running?
ZURG_USERNAME=riven                 # Username (if auth enabled)
ZURG_PASSWORD=12345                 # Password (if auth enabled)

# ============================================================================
# FILE PERMISSIONS
# ============================================================================
PUID=1000                           # Your user ID (run: id -u)
PGID=1000                           # Your group ID (run: id -g)

# ============================================================================
# MONITORING BEHAVIOR
# ============================================================================
CHECK_INTERVAL=30                   # How often to check (minutes)
RATE_LIMIT=10                       # Requests before backing off

# ============================================================================
# LOGGING VERBOSITY
# ============================================================================
VERBOSE=false                       # Show INFO messages (true/false)
DEBUG=false                         # Show DEBUG messages (true/false)
TRACE=false                         # Show TRACE messages (true/false)

# ============================================================================
# RUNTIME MODE
# ============================================================================
RUN_ONCE=false                      # Run once and exit (true/false)
DRY_RUN=false                       # Don't trigger repairs (true/false)

# ============================================================================
# TIMEZONE
# ============================================================================
TZ=UTC                              # Your timezone
```

## Common Scenarios

### Scenario 1: Zurg on Same Docker Network

```bash
# .env
ZURG_URL=http://zurg:9999
PUID=1000
PGID=1000
```

### Scenario 2: Zurg on Host Machine

```bash
# .env
ZURG_URL=http://host.docker.internal:9999
PUID=1000
PGID=1000
```

### Scenario 3: Zurg on Different Machine

```bash
# .env
ZURG_URL=http://192.168.1.100:9999
PUID=1000
PGID=1000
```

### Scenario 4: With Authentication

```bash
# .env
ZURG_URL=http://zurg:9999
ZURG_USERNAME=admin
ZURG_PASSWORD=secretpassword
PUID=1000
PGID=1000
```

### Scenario 5: Testing/Debug Mode

```bash
# .env
ZURG_URL=http://zurg:9999
PUID=1000
PGID=1000
RUN_ONCE=true
DRY_RUN=true
VERBOSE=true
DEBUG=true
```

### Scenario 6: High Frequency Monitoring

```bash
# .env
ZURG_URL=http://zurg:9999
PUID=1000
PGID=1000
CHECK_INTERVAL=10
RATE_LIMIT=20
VERBOSE=true
```

## Timezone Settings

Common timezone values:

```bash
# Americas
TZ=America/New_York
TZ=America/Chicago
TZ=America/Denver
TZ=America/Los_Angeles
TZ=America/Toronto

# Europe
TZ=Europe/London
TZ=Europe/Paris
TZ=Europe/Berlin
TZ=Europe/Amsterdam

# Asia
TZ=Asia/Tokyo
TZ=Asia/Shanghai
TZ=Asia/Dubai
TZ=Asia/Kolkata

# Australia
TZ=Australia/Sydney
TZ=Australia/Melbourne

# UTC
TZ=UTC
```

Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Validation

### Check if .env is loaded

```bash
# View environment in running container
docker exec zurg-monitor env | grep ZURG
docker exec zurg-monitor env | grep PUID
docker exec zurg-monitor env | grep PGID
```

### Check file permissions

```bash
# Check log file ownership
ls -la logs/
# Should show your user:group

# From inside container
docker exec zurg-monitor ls -la /logs/
```

### Verify settings

```bash
# Check container logs
docker-compose logs zurg-monitor

# Should see:
# Starting with UID:1000, GID:1000
# Using Zurg URL from environment: http://zurg:9999
```

## Troubleshooting

### Permission Denied Errors

```bash
# Check current permissions
ls -la logs/ config/

# Fix permissions
sudo chown -R $(id -u):$(id -g) logs/ config/

# Or in .env, match your actual IDs
PUID=$(id -u)
PGID=$(id -g)
```

### PUID/PGID Not Applied

```bash
# Recreate container
docker-compose down
docker-compose up -d

# Check user in container
docker exec zurg-monitor id
```

### .env Not Loaded

```bash
# Make sure .env is in same directory as docker-compose.yml
ls -la .env

# Make sure it's not .env.sample
mv .env.sample .env

# Restart
docker-compose down
docker-compose up -d
```

### Cannot Connect to Zurg

```bash
# Test from container
docker exec zurg-monitor curl http://zurg:9999/stats

# If fails, check ZURG_URL in .env
# Try: host.docker.internal:9999 or actual IP
```

## Security Best Practices

### 1. Protect Your .env File

```bash
# Set proper permissions
chmod 600 .env

# Never commit to git
echo ".env" >> .gitignore

# Use .env.sample as template
git add .env.sample
```

### 2. Use Docker Secrets (Production)

Instead of .env for passwords:

```yaml
# docker-compose.yml
services:
  zurg-monitor:
    secrets:
      - zurg_password
    environment:
      - ZURG_PASSWORD_FILE=/run/secrets/zurg_password

secrets:
  zurg_password:
    file: ./secrets/zurg_password.txt
```

### 3. Separate Sensitive Data

```bash
# Create separate files
echo "secretpassword" > .zurg_password
chmod 600 .zurg_password

# Reference in docker-compose
environment:
  - ZURG_PASSWORD_FILE=/.zurg_password
```

## Complete Example

```bash
# 1. Setup directory
mkdir -p ~/zurg-monitor
cd ~/zurg-monitor

# 2. Get files
# (download or clone repository)

# 3. Create .env
cat > .env << 'EOF'
ZURG_URL=http://zurg:9999
ZURG_USERNAME=riven
ZURG_PASSWORD=12345
PUID=1000
PGID=1000
CHECK_INTERVAL=30
RATE_LIMIT=10
VERBOSE=false
DEBUG=false
TZ=America/New_York
EOF

# 4. Set correct IDs
sed -i "s/PUID=1000/PUID=$(id -u)/" .env
sed -i "s/PGID=1000/PGID=$(id -g)/" .env

# 5. Create directories
mkdir -p config logs

# 6. Copy config
cp zurg-monitor.conf config/

# 7. Build and start
docker-compose build
docker-compose up -d

# 8. Check logs
docker-compose logs -f zurg-monitor

# 9. Verify files
ls -la logs/ config/
# Should be owned by your user
```

## Environment Variable Priority

Settings are applied in this order (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **Environment variables** (.env file)
3. **Configuration file** (zurg-monitor.conf)
4. **Built-in defaults** (lowest priority)

Example:
```bash
# In .env
CHECK_INTERVAL=30

# In docker-compose.yml environment section
CHECK_INTERVAL=60

# docker-compose.yml wins (60 minutes)
```

## Quick Commands

```bash
# Edit .env
nano .env

# Reload changes
docker-compose down
docker-compose up -d

# View current environment
docker exec zurg-monitor env

# Check file ownership
docker exec zurg-monitor ls -la /logs /config

# Test connection
docker exec zurg-monitor curl http://zurg:9999/stats
```

---

**Remember**: Always use `.env.sample` as a template and never commit `.env` with real passwords to version control!