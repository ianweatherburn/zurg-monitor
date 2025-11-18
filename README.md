# Zurg Broken Torrent Monitor - Python Edition

A Python implementation of the [Zurg](https://github.com/debridmediamanager/zurg-testing) Broken Torrent Monitor & Repair Tool for Linux systems. 
This is a rewrite of the PowerShell script written by [@madguru](https://github.com/maddguru) which can be found in his [zurg-broken-torrent-monitor](https://github.com/maddguru/zurg-broken-torrent-monitor) and all credit goes to [MaddGuru](https://github.com/maddguru).

## What is it?
This free tool can continuously monitor your Zurg instance for broken and under-repair torrents, automatically triggers repairs, and provide detailed statistics about your entire torrent library's health.
For more detail on [Zurg](https://github.com/debridmediamanager/zurg-testing) which is a self-hosted Real-Debrid WebDAV server, see the [Zurg](https://github.com/debridmediamanager/zurg-testing) repo and sponsor [@yomamasita](https://paypal.me/yowmamasita) for his amazing utility.
_This tool is only needed as an interim measure while the Zurg repair tool is undergoing maintenance._


## Features

- 🔍 **Automatic Detection**: Continuously monitors for broken and under-repair torrents
- 🔧 **Automatic Repair**: Triggers repair operations for broken torrents
- 📊 **Detailed Statistics**: Tracks repair success rates and historical data
- 🚦 **Rate Limiting**: Prevents API overload with configurable rate limits
- 📝 **Comprehensive Logging**: Rotating logs with trace/debug support
- 🎯 **Dry Run Mode**: Test operations without triggering actual repairs
- ⚙️ **Flexible Configuration**: INI config file + CLI argument support
- 🔄 **Run Modes**: Single-check or continuous monitoring
- 🐧 **Linux Native**: Built for Linux with systemd support

## Requirements

- Python 3.10 or higher
- Zurg server (v0.9.3+ recommended)
- Standard Python libraries (no external dependencies required)

## Installation

### Quick Install

```bash
# 1. Create installation directory
sudo mkdir -p /opt/zurg-monitor
cd /opt/zurg-monitor

# 2. Download the script and config file
# (Copy zurg-monitor.py and zurg-monitor.conf to this directory)

# 3. Make the script executable
sudo chmod +x zurg-monitor.py

# 4. Edit the configuration file
sudo nano zurg-monitor.conf
```

### Configuration File Locations

The monitor searches for configuration files in this order:

1. Path specified with `-c/--config` argument
2. `./zurg-monitor.conf` (current directory)
3. `~/.config/zurg-monitor/zurg-monitor.conf`
4. `/etc/zurg-monitor/zurg-monitor.conf`

### Basic Configuration

Edit `zurg-monitor.conf`:

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

## Usage

### Command-Line Options

```
Options:
  -h, --help            Show help message
  -v, --version         Show version
  -c, --config PATH     Path to configuration file
  -u, --zurg-url URL    Zurg URL (overrides config)
  --username USER       Authentication username
  --password PASS       Authentication password
  -i, --check-interval N    Check interval in minutes
  -l, --log-file PATH   Log file path
  -r, --rate-limit N    Requests before backoff
  --run-once            Run single check and exit
  -t, --trace           Enable trace logging (very verbose)
  -d, --debug           Enable debug logging
  --dry-run             Show what would be done without repairs
```

### Examples

#### Single Check (Test Mode)
```bash
# Run once with default config
python3 zurg-monitor.py --run-once

# Run once with dry-run (no actual repairs)
python3 zurg-monitor.py --run-once --dry-run

# Run once with debug output
python3 zurg-monitor.py --run-once --debug
```

#### Continuous Monitoring
```bash
# Run continuously with default settings
python3 zurg-monitor.py

# Run with custom check interval (60 minutes)
python3 zurg-monitor.py --check-interval 60

# Run with custom Zurg URL
python3 zurg-monitor.py --zurg-url http://192.168.1.100:9999
```

#### Advanced Usage
```bash
# Trace mode for debugging (very verbose)
python3 zurg-monitor.py --run-once --trace

# Custom rate limiting
python3 zurg-monitor.py --rate-limit 5

# Use custom config file
python3 zurg-monitor.py --config /etc/my-zurg-config.conf
```

## Running as a Service

### Install systemd Service

```bash
# 1. Copy the service file
sudo cp zurg-monitor.service /etc/systemd/system/

# 2. Edit the service file to match your paths
sudo nano /etc/systemd/system/zurg-monitor.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable the service (start on boot)
sudo systemctl enable zurg-monitor

# 5. Start the service
sudo systemctl start zurg-monitor

# 6. Check status
sudo systemctl status zurg-monitor

# 7. View logs
sudo journalctl -u zurg-monitor -f
```

### Service Management

```bash
# Start service
sudo systemctl start zurg-monitor

# Stop service
sudo systemctl stop zurg-monitor

# Restart service
sudo systemctl restart zurg-monitor

# Check status
sudo systemctl status zurg-monitor

# View logs (follow mode)
sudo journalctl -u zurg-monitor -f

# View logs (last 100 lines)
sudo journalctl -u zurg-monitor -n 100

# Disable service (don't start on boot)
sudo systemctl disable zurg-monitor
```

## Logging

### Log Rotation

- Logs are automatically rotated
- Maximum of 10 log files kept
- Each log file can be up to 10MB
- Old logs are automatically deleted

### Log Levels

- **Normal**: Standard operation messages
- **Debug** (`--debug`): Additional operational details
- **Trace** (`--trace`): Extensive execution details

### Example Log Output

```
[2025-11-14 10:30:00] [INFO] Starting torrent status check...
[2025-11-14 10:30:01] [DEBUG] Fetching broken torrents from Zurg...
[2025-11-14 10:30:02] [INFO] Found 2 broken torrent(s)
[2025-11-14 10:30:02] [INFO] Found 1 under repair torrent(s)
[2025-11-14 10:30:03] [SUCCESS] Successfully triggered repair for: Movie.Name.2024
[2025-11-14 10:30:04] [INFO] Torrent status check completed
```

## Rate Limiting

The monitor implements intelligent rate limiting to prevent API overload:

- **rate_limit**: Number of requests before backing off (default: 10)
- **rate_limit_delay**: Delay between requests in seconds (default: 0.5)
- **rate_limit_backoff**: Backoff time after hitting limit (default: 5)

Example configuration:
```ini
rate_limit = 15              # Make 15 requests
rate_limit_delay = 0.3       # Wait 0.3s between requests
rate_limit_backoff = 10      # Back off for 10s after limit
```

## Statistics and Reporting

### Check Summary

Each check provides:
- Total torrents count
- OK torrents (with percentage)
- Broken torrents (with percentage)
- Under repair torrents (with percentage)
- Repairs triggered count
- Comparison with previous check
- Repair success rate

### Overall Statistics

Track across multiple checks:
- Total checks performed
- Total broken torrents found
- Total repairs triggered
- Last check timestamp
- Last broken torrent timestamp

## Troubleshooting

### Connection Issues

```bash
# Test connection manually
curl http://localhost:9999/stats

# Check if Zurg is running
sudo systemctl status zurg

# Verify network connectivity
ping localhost
```

### Permission Issues

```bash
# Make script executable
chmod +x zurg-monitor.py

# Check log file permissions
ls -la zurg-monitor.log

# Create log directory if needed
mkdir -p /var/log/zurg-monitor
```

### Service Not Starting

```bash
# Check service logs
sudo journalctl -u zurg-monitor -n 50

# Verify Python version
python3 --version

# Check if script path is correct
cat /etc/systemd/system/zurg-monitor.service

# Test script manually
python3 /opt/zurg-monitor/zurg-monitor.py --run-once --debug
```

### Enable Debug Logging

```bash
# Run with debug output
python3 zurg-monitor.py --run-once --debug

# Run with trace output (very verbose)
python3 zurg-monitor.py --run-once --trace
```

## Differences from PowerShell Version

### Improvements

1. **Log Rotation**: Automatic log rotation (10 files max)
2. **Rate Limiting**: Enhanced rate limiting with configurable backoff
3. **Configuration**: Standard INI format with multiple search paths
4. **Service Integration**: Native systemd support
5. **Error Handling**: More robust error handling and recovery
6. **No External Dependencies**: Uses only Python standard library

### Feature Parity

All features from the PowerShell version are implemented:
- ✅ Broken torrent detection
- ✅ Under repair monitoring
- ✅ Automatic repair triggering
- ✅ Statistics tracking
- ✅ Authentication support
- ✅ Single-run and continuous modes
- ✅ Comprehensive logging

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project maintains the same license as the original PowerShell version.

## Credits

Python port based on the original PowerShell script:
- Original Repository: https://github.com/maddguru/zurg-broken-torrent-monitor

## Support

For issues and questions:
- Check the troubleshooting section above
- Review logs with `--debug` or `--trace` flags
- Verify Zurg server is accessible
- Check the original repository for Zurg-specific issues

## Version History

### v3.0.0 (Python Edition)
- Initial Python implementation
- Added rate limiting with configurable backoff
- Added log rotation
- Added trace/debug logging modes
- Added dry-run mode
- Added systemd service support
- INI configuration file format