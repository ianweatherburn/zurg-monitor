# Changelog

## Version 3.0.0 - Latest Changes

### Major Updates

#### 1. **Log Directory Management**
- ✅ Logs now default to `./logs/` directory relative to script location
- ✅ Directory is automatically created if it doesn't exist
- ✅ Path: `./logs/zurg-monitor.log`

#### 2. **Docker PUID/PGID Support**
- ✅ Added support for `PUID` and `PGID` environment variables
- ✅ Proper file permissions applied to logs and config
- ✅ Script can change process UID/GID when running as root
- ✅ Dockerfile entrypoint handles user/group creation
- ✅ Works with `user: "${PUID}:${PGID}"` in docker-compose

#### 3. **Environment Configuration**
- ✅ Created `.env.sample` file with all configurable variables
- ✅ Updated `docker-compose.yml` to use `.env` file
- ✅ All environment variables documented
- ✅ Production-ready configuration

#### 4. **Console Output Improvements**
- ✅ Removed duplicate banner output
- ✅ Removed duplicate "CHECK SUMMARY" output  
- ✅ INFO messages suppressed by default on console
- ✅ INFO messages always written to log file
- ✅ Cleaner, less verbose output

#### 5. **Verbose Mode**
- ✅ Added `-v`/`--verbose` command-line option
- ✅ Added `verbose` configuration file option
- ✅ When enabled, shows INFO messages on console
- ✅ INFO always logged to file regardless of setting

#### 6. **Enhanced Logging**
- ✅ Debug and trace messages now written to log file
- ✅ Check summary output written to log file
- ✅ Overall statistics written to log file
- ✅ Complete audit trail in logs
- ✅ Console vs file logging properly separated

#### 7. **Version Management**
- ✅ Version moved to global `VERSION` variable
- ✅ Script name in global `SCRIPT_NAME` variable
- ✅ Easy to update in one location
- ✅ Used consistently throughout code

#### 8. **File Naming**
- ✅ Script renamed to `zurg-monitor.py`
- ✅ All references updated in:
  - Dockerfile
  - docker-compose.yml
  - Makefile
  - build-docker.sh
  - Documentation
  - README files

#### 9. **Requirements Documentation**
- ✅ Created `requirements.txt`
- ✅ Documents that only standard library is used
- ✅ Lists all Python modules utilized
- ✅ No pip install needed

### Configuration Files Added

1. **`.env.sample`** - Environment variables template
2. **`requirements.txt`** - Python dependencies (none needed)
3. **`CHANGELOG.md`** - This file

### Updated Files

1. **`zurg-monitor.py`**
   - Version management
   - Log directory handling
   - PUID/PGID support
   - Verbose mode
   - Enhanced logging
   - Fixed duplicate output

2. **`zurg-monitor.conf`**
   - Added verbose option
   - Updated default log path
   - Enhanced documentation

3. **`docker-compose.yml`**
   - Uses `.env` file
   - PUID/PGID support
   - VERBOSE environment variable
   - Production-ready configuration
   - Better documentation

4. **`Dockerfile`**
   - PUID/PGID handling in entrypoint
   - VERBOSE flag support
   - User/group management
   - Proper permissions

5. **`Makefile`**
   - Updated all references to zurg-monitor.py

6. **`build-docker.sh`**
   - Updated all references to zurg-monitor.py

7. **All Documentation**
   - Updated references to new filename
   - Added .env file documentation
   - Added PUID/PGID documentation
   - Added verbose mode documentation

### Bug Fixes

- ✅ Fixed duplicate banner output to console
- ✅ Fixed duplicate check summary output
- ✅ Fixed debug/trace not logging to file
- ✅ Fixed statistics not logging to file
- ✅ Fixed log directory not being created

### Command-Line Options

#### New Options
- `-v, --verbose` - Show INFO messages on console

#### All Options
```bash
-c, --config PATH        Configuration file path
-u, --zurg-url URL       Zurg URL
--username USER          Authentication username
--password PASS          Authentication password
-i, --check-interval N   Check interval in minutes
-l, --log-file PATH      Log file path
--run-once               Run single check and exit
-v, --verbose            Show INFO messages (NEW)
-t, --trace              Enable trace logging
-d, --debug              Enable debug logging
--dry-run                Dry run mode
-r, --rate-limit N       Rate limit requests
--version                Show version
```

### Environment Variables

#### New Variables
- `PUID` - User ID for file permissions
- `PGID` - Group ID for file permissions
- `VERBOSE` - Enable verbose console output

#### All Variables
```bash
ZURG_URL         # Zurg server URL
ZURG_USERNAME    # Authentication username
ZURG_PASSWORD    # Authentication password
CHECK_INTERVAL   # Check interval in minutes
RATE_LIMIT       # Rate limit requests
PUID             # User ID (NEW)
PGID             # Group ID (NEW)
RUN_ONCE         # Run once mode
VERBOSE          # Verbose output (NEW)
DEBUG            # Debug mode
TRACE            # Trace mode
DRY_RUN          # Dry run mode
TZ               # Timezone
```

### Configuration File Options

#### New Options
- `verbose` - Enable verbose console output

#### All Options
```ini
[zurg]
zurg_url             # Zurg server URL
username             # Authentication username
password             # Authentication password
check_interval       # Check interval in minutes
log_file             # Log file path (default: ./logs/zurg-monitor.log)
verbose              # Verbose console output (NEW)
rate_limit           # Rate limit requests
rate_limit_delay     # Delay between requests
rate_limit_backoff   # Backoff time after limit
```

### Migration Guide

#### From Previous Version

1. **Update Script Name**
   ```bash
   mv zurg_monitor_py.py zurg-monitor.py
   ```

2. **Update Config File**
   ```ini
   # Add to zurg-monitor.conf
   verbose = false
   
   # Update log_file path if needed
   log_file = ./logs/zurg-monitor.log
   ```

3. **Create .env File (Docker)**
   ```bash
   cp .env.sample .env
   nano .env  # Edit values
   ```

4. **Update docker-compose.yml**
   ```bash
   # Pull latest docker-compose.yml
   # Add PUID/PGID to environment
   user: "${PUID}:${PGID}"
   ```

5. **Rebuild Docker Image**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Testing

To test all new features:

```bash
# Test verbose mode
python3 zurg-monitor.py --run-once --verbose

# Test log directory creation
rm -rf logs
python3 zurg-monitor.py --run-once

# Test PUID/PGID (Docker)
PUID=1001 PGID=1001 docker-compose up

# Test .env file (Docker)
docker-compose up -d
docker-compose logs -f
```

### Known Issues

None currently.

### Future Enhancements

- [ ] Add Prometheus metrics endpoint
- [ ] Add web dashboard
- [ ] Add email notifications
- [ ] Add webhook support
- [ ] Add scheduling options beyond fixed intervals

---

## Previous Versions

### Version 2.2.1 (PowerShell)
- Original PowerShell implementation
- Windows-focused
- Basic monitoring and repair

### Version 3.0.0 (Python - Initial)
- Python port of PowerShell version
- Linux-focused
- Docker support
- Enhanced logging
- Rate limiting
- Multiple deployment options