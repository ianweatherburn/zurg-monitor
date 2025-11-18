# Zurg Monitor - Quick Reference Guide

## Quick Start

```bash
# Install
sudo bash install.sh

# Edit config
sudo nano /etc/zurg-monitor/zurg-monitor.conf

# Test run
zurg-monitor --run-once --debug

# Start continuous monitoring
zurg-monitor
```

## Common Commands

### One-Time Checks
```bash
# Basic check
zurg-monitor --run-once

# Check with debug output
zurg-monitor --run-once --debug

# Dry run (no repairs)
zurg-monitor --run-once --dry-run

# Full trace logging
zurg-monitor --run-once --trace
```

### Continuous Monitoring
```bash
# Default (30 min intervals)
zurg-monitor

# Custom interval (60 minutes)
zurg-monitor --check-interval 60

# Custom Zurg URL
zurg-monitor --zurg-url http://192.168.1.100:9999
```

### Service Management
```bash
# Start
sudo systemctl start zurg-monitor

# Stop
sudo systemctl stop zurg-monitor

# Restart
sudo systemctl restart zurg-monitor

# Status
sudo systemctl status zurg-monitor

# Enable on boot
sudo systemctl enable zurg-monitor

# Disable on boot
sudo systemctl disable zurg-monitor

# View logs (live)
sudo journalctl -u zurg-monitor -f

# View logs (last 100)
sudo journalctl -u zurg-monitor -n 100
```

## Configuration File

**Location**: `/etc/zurg-monitor/zurg-monitor.conf`

```ini
[zurg]
zurg_url = http://localhost:9999
username = riven
password = 12345
check_interval = 30
log_file = zurg-monitor.log
rate_limit = 10
rate_limit_delay = 0.5
rate_limit_backoff = 5
```

## Command-Line Arguments

| Short | Long | Description |
|-------|------|-------------|
| `-h` | `--help` | Show help |
| `-v` | `--version` | Show version |
| `-c` | `--config PATH` | Config file path |
| `-u` | `--zurg-url URL` | Zurg URL |
|  | `--username USER` | Auth username |
|  | `--password PASS` | Auth password |
| `-i` | `--check-interval N` | Check interval (minutes) |
| `-l` | `--log-file PATH` | Log file path |
| `-r` | `--rate-limit N` | Rate limit requests |
|  | `--run-once` | Single check mode |
| `-t` | `--trace` | Trace logging |
| `-d` | `--debug` | Debug logging |
|  | `--dry-run` | Dry run mode |

## Troubleshooting

### Can't Connect to Zurg
```bash
# Test manually
curl http://localhost:9999/stats

# Check Zurg status
sudo systemctl status zurg

# Verify in config
cat /etc/zurg-monitor/zurg-monitor.conf
```

### Permission Denied
```bash
# Make executable
chmod +x /opt/zurg-monitor/zurg-monitor.py

# Fix log permissions
sudo chown $(whoami) zurg-monitor.log
```

### Service Won't Start
```bash
# Check logs
sudo journalctl -u zurg-monitor -n 50

# Test manually
python3 /opt/zurg-monitor/zurg-monitor.py --run-once --debug

# Verify paths in service
cat /etc/systemd/system/zurg-monitor.service

# Reload systemd
sudo systemctl daemon-reload
```

### Python Version Issues
```bash
# Check version
python3 --version

# Minimum required: Python 3.10
```

## Rate Limiting Explained

The monitor uses intelligent rate limiting:

1. **rate_limit** (default: 10)
   - Number of API requests before backing off
   - Example: After 10 requests, pause

2. **rate_limit_delay** (default: 0.5)
   - Seconds to wait between each request
   - Example: 0.5s = half second delay

3. **rate_limit_backoff** (default: 5)
   - Seconds to wait after hitting rate limit
   - Example: After 10 requests, wait 5 seconds

### Example Scenarios

**Conservative (slow but safe)**:
```ini
rate_limit = 5
rate_limit_delay = 1.0
rate_limit_backoff = 10
```

**Balanced (default)**:
```ini
rate_limit = 10
rate_limit_delay = 0.5
rate_limit_backoff = 5
```

**Aggressive (fast but may overwhelm)**:
```ini
rate_limit = 20
rate_limit_delay = 0.2
rate_limit_backoff = 2
```

## Log Levels

| Level | Flag | Description |
|-------|------|-------------|
| Normal | (none) | Standard operation |
| Debug | `-d` or `--debug` | Detailed steps |
| Trace | `-t` or `--trace` | Full execution details |

## File Locations

### System-Wide Installation
```
/opt/zurg-monitor/zurg-monitor.py          # Main script
/etc/zurg-monitor/zurg-monitor.conf        # Configuration
/etc/systemd/system/zurg-monitor.service   # Service file
/usr/local/bin/zurg-monitor                # Symlink
```

### User Installation
```
~/.local/share/zurg-monitor/zurg-monitor.py    # Main script
~/.config/zurg-monitor/zurg-monitor.conf       # Configuration
```

## Output Examples

### Healthy Library
```
✓ No broken or under repair torrents found - library is healthy!
```

### Broken Torrents Found
```
Found 2 broken torrent(s)
Found 1 under repair torrent(s)

BROKEN TORRENTS:
  - Movie.Name.2024.1080p.BluRay
  - TV.Show.S01E01.1080p.WEB

Triggering repairs...
Successfully triggered repair for: Movie.Name.2024.1080p.BluRay
Successfully triggered repair for: TV.Show.S01E01.1080p.WEB
```

### Statistics Summary
```
CHECK SUMMARY
═════════════════════════════════════════════════════════════════════

TORRENT STATISTICS:
  Total Torrents:            150
  OK Torrents:               145 (96.67%)
  Broken:                    3 (2.0%)
  Under Repair:              2 (1.33%)

CURRENT CHECK RESULTS:
  Broken Torrents:           3
  Under Repair:              2
  Repairs Triggered:         5

COMPARISON WITH PREVIOUS CHECK:
  Successfully Repaired:     2
  Moved to Repair:           1
  Still Broken:              1
  Still Under Repair:        1
  New Broken:                1
  Repair Success Rate:       66.7%
```

## Best Practices

1. **Start with --dry-run** to test before triggering repairs
2. **Use --debug** for initial troubleshooting
3. **Monitor logs** regularly with `journalctl -f`
4. **Adjust rate limiting** based on your Zurg instance
5. **Run system-wide** for always-on monitoring
6. **Back up config** before major changes

## Common Use Cases

### Initial Testing
```bash
zurg-monitor --run-once --dry-run --debug
```

### Production Monitoring
```bash
sudo systemctl enable zurg-monitor
sudo systemctl start zurg-monitor
```

### Troubleshooting Issues
```bash
zurg-monitor --run-once --trace
```

### Custom Schedule
```bash
# Check every 2 hours
zurg-monitor --check-interval 120
```

### Different Server
```bash
zurg-monitor --zurg-url http://server:9999 --username user --password pass
```

## Support

- **Documentation**: README.md
- **Original Project**: https://github.com/maddguru/zurg-broken-torrent-monitor
- **Logs**: Check with `--debug` or `--trace` flags
- **Service Logs**: `sudo journalctl -u zurg-monitor`