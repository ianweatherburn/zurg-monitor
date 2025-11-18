#!/usr/bin/env python3
"""
Zurg Broken Torrent Monitor & Repair Tool
Python implementation for Linux systems
"""

import argparse
import base64
import configparser
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from html import unescape
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import quote

try:
    import urllib.request
    import urllib.error
    from http.client import HTTPResponse
except ImportError as e:
    print(f"Error: Missing required standard library: {e}")
    sys.exit(1)

# Version information
VERSION = "1.0.0"
SCRIPT_NAME = "Zurg Broken Torrent Monitor"


class LogLevel(Enum):
    """Log level enumeration"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    OUTPUT = "OUTPUT"

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


@dataclass
class TorrentInfo:
    """Torrent information structure"""
    hash: str
    name: str
    state: str


@dataclass
class CheckStats:
    """Statistics for a single check"""
    broken_found: int = 0
    under_repair_found: int = 0
    repairs_triggered: int = 0
    broken_hashes: List[str] = field(default_factory=list)
    broken_names: List[str] = field(default_factory=list)
    under_repair_hashes: List[str] = field(default_factory=list)
    under_repair_names: List[str] = field(default_factory=list)
    total_torrents: int = 0
    ok_torrents: int = 0


@dataclass
class OverallStats:
    """Overall monitoring statistics"""
    total_checks: int = 0
    broken_found: int = 0
    under_repair_found: int = 0
    repairs_triggered: int = 0
    last_check: Optional[datetime] = None
    last_broken_found: Optional[datetime] = None
    current_check: CheckStats = field(default_factory=CheckStats)
    previous_check_broken: List[str] = field(default_factory=list)
    previous_check_under_repair: List[str] = field(default_factory=list)
    previous_check_triggered: List[str] = field(default_factory=list)


class ZurgMonitor:
    """Main Zurg monitoring class"""

    def __init__(self, config: Dict, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.stats = OverallStats()
        self.logger = self._setup_logger()
        self.rate_limit_delay = config.get('rate_limit_delay', 0.5)
        self.rate_limit_requests = config.get('rate_limit_requests', 10)
        self.request_count = 0
        
        # Apply PUID/PGID if specified (for Docker)
        self._apply_permissions()

    def _apply_permissions(self):
        """Apply PUID/PGID permissions if specified"""
        puid = os.environ.get('PUID')
        pgid = os.environ.get('PGID')
        
        if puid and pgid:
            try:
                puid = int(puid)
                pgid = int(pgid)
                # Change process UID/GID if running as root
                if os.geteuid() == 0:
                    os.setgid(pgid)
                    os.setuid(puid)
                    self._log(f"Applied permissions: UID={puid}, GID={pgid}", LogLevel.DEBUG)
            except (ValueError, PermissionError) as e:
                self._log(f"Could not apply PUID/PGID: {e}", LogLevel.WARN, Colors.YELLOW)

    def _setup_logger(self) -> logging.Logger:
        """Setup logging with rotation"""
        logger = logging.getLogger('ZurgMonitor')
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Set base level to capture everything
        logger.setLevel(logging.DEBUG)

        # # Console handler - filtered based on verbosity
        # console_handler = logging.StreamHandler(sys.stdout)
        # if self.config.get('trace'):
        #     console_handler.setLevel(logging.TRACE)
        # elif self.config.get('debug'):
        #     console_handler.setLevel(logging.DEBUG)
        # elif self.config.get('verbose'):
        #     console_handler.setLevel(logging.INFO)
        # else:
        #     # Suppress INFO by default on console
        #     console_handler.setLevel(logging.WARNING)
        
        # console_formatter = logging.Formatter('%(message)s')
        # console_handler.setFormatter(console_formatter)
        # logger.addHandler(console_handler)

        # File handler with rotation - always logs everything
        log_file = Path(self.config['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Apply permissions to log directory if PUID/PGID set
        self._set_directory_permissions(log_file.parent)
        
        # Rotate logs: max 10 files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB per file
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def _set_directory_permissions(self, directory: Path):
        """Set directory permissions based on PUID/PGID"""
        puid = os.environ.get('PUID')
        pgid = os.environ.get('PGID')
        
        if puid and pgid:
            try:
                puid = int(puid)
                pgid = int(pgid)
                if directory.exists():
                    os.chown(directory, puid, pgid)
            except (ValueError, PermissionError, OSError):
                pass  # Silently ignore permission errors

    def _log(self, message: str, level: LogLevel = LogLevel.INFO, color: Colors = Colors.GRAY):
        """Custom logging with colors"""
        # Map to logging levels
        level_map = {
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.SUCCESS: logging.INFO,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.OUTPUT: logging.INFO,
        }

        # Color map
        color_map = {
            LogLevel.INFO: Colors.CYAN,
            LogLevel.WARN: Colors.YELLOW,
            LogLevel.ERROR: Colors.RED,
            LogLevel.SUCCESS: Colors.GREEN,
            LogLevel.DEBUG: Colors.GRAY,
            LogLevel.TRACE: Colors.GRAY,
            LogLevel.OUTPUT: Colors.GRAY,
        }

        # Determine if should log to file and print to console
        should_log = False
        should_print = False

        if level == LogLevel.TRACE:
            # TRACE: Only if trace is ON
            if self.config.get('trace'):
                should_log = True
                should_print = True
            # else: no output at all
        
        elif level == LogLevel.DEBUG:
            # DEBUG: Only if debug OR trace is ON
            if self.config.get('debug') or self.config.get('trace'):
                should_log = True
                should_print = True
            # else: no output at all
        
        elif level == LogLevel.INFO:
            # INFO: ALWAYS log to file, only print to console if verbose is ON
            should_log = True
            if self.config.get('verbose') or self.config.get('debug') or self.config.get('trace'):
                should_print = True
        
        elif level in [LogLevel.WARN, LogLevel.ERROR, LogLevel.SUCCESS]:
            # WARN/ERROR/SUCCESS: Always log and print
            should_log = True
            should_print = True

        elif level == LogLevel.OUTPUT:
            # OUTPUT: Always log and print (like WARN/ERROR/SUCCESS)
            should_log = True
            should_print = True

        # Log to file if appropriate
        if should_log:
            self.logger.log(level_map[level], message)
        
        # Print to console with colors if appropriate
        if should_print:
            # color = color_map.get(level, Colors.RESET)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if level == LogLevel.OUTPUT:
                print(f"{color}[{timestamp}] {message}{Colors.RESET}")
            else:
                print(f"{color}[{timestamp}] [{level.value}] {message}{Colors.RESET}")

    def _log_banner(self, text: str):
        """Log a banner"""
        line = "=" * 72
        
        self._log("", LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(line, LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(f"  {text}", LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(line, LogLevel.OUTPUT, Colors.MAGENTA)
        self._log("", LogLevel.OUTPUT, Colors.MAGENTA)

    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        self.request_count += 1
        if self.request_count >= self.rate_limit_requests:
            backoff_time = self.config.get('rate_limit_backoff', 5)
            self._log(f"Rate limit reached ({self.rate_limit_requests} requests), backing off for {backoff_time}s...", 
                     LogLevel.DEBUG)
            time.sleep(backoff_time)
            self.request_count = 0
        else:
            time.sleep(self.rate_limit_delay)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"ZurgMonitor/{VERSION}"
        }

        username = self.config.get('username')
        password = self.config.get('password')

        if username and password:
            credentials = f"{username}:{password}"
            b64_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {b64_credentials}"
            self._log(f"Using authentication for user: {username}", LogLevel.TRACE)

        return headers

    def _make_request(self, url: str, method: str = "GET", timeout: int = 30) -> Optional[bytes]:
        """Make HTTP request with error handling"""
        try:
            self._log(f"Making {method} request to: {url}", LogLevel.TRACE)
            headers = self._get_auth_headers()
            
            request = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read()
                self._log(f"Request successful, received {len(content)} bytes", LogLevel.TRACE)
                return content

        except urllib.error.HTTPError as e:
            self._log(f"HTTP Error {e.code}: {e.reason} for URL: {url}", LogLevel.ERROR, Colors.RED)
            return None
        except urllib.error.URLError as e:
            self._log(f"URL Error: {e.reason} for URL: {url}", LogLevel.ERROR, Colors.RED)
            return None
        except Exception as e:
            self._log(f"Unexpected error: {str(e)} for URL: {url}", LogLevel.ERROR, Colors.RED)
            return None

    def test_connection(self) -> bool:
        """Test connection to Zurg"""
        try:
            self._log(f"Testing connection to Zurg at {self.config['zurg_url']}...", LogLevel.DEBUG)
            url = f"{self.config['zurg_url']}/stats"
            
            content = self._make_request(url, timeout=10)
            if content:
                self._log("Successfully connected to Zurg", LogLevel.SUCCESS, Colors.GREEN)
                return True
            else:
                self._log("Failed to connect to Zurg", LogLevel.ERROR, Colors.RED)
                return False

        except Exception as e:
            self._log(f"Connection test failed: {str(e)}", LogLevel.ERROR, Colors.RED)
            return False

    def _parse_torrents_from_html(self, content: str, state: str) -> List[TorrentInfo]:
        """Parse torrents from HTML content"""
        state_name = "broken" if state == "status_broken" else "under repair"
        self._log(f"Parsing {state_name} torrents from HTML...", LogLevel.TRACE)
        
        torrents = []
        processed_hashes: Set[str] = set()

        # Pattern 1: Look for table rows with data-hash
        row_pattern = r'<tr[^>]*data-hash="([a-fA-F0-9]{40})"[^>]*>'
        row_matches = re.finditer(row_pattern, content)
        
        row_count = 0
        for match in row_matches:
            row_count += 1
            hash_value = match.group(1).lower()
            
            if hash_value in processed_hashes:
                continue
            processed_hashes.add(hash_value)

            # Extract the row content
            row_start = match.start()
            row_end = content.find('</tr>', row_start)
            if row_end == -1:
                row_end = min(len(content), row_start + 2000)
            row_content = content[row_start:row_end]

            # Try to find torrent name
            torrent_name = self._extract_torrent_name(row_content, hash_value)
            
            self._log(f"  Found {state_name} torrent: {torrent_name}", LogLevel.TRACE)
            
            torrents.append(TorrentInfo(
                hash=hash_value,
                name=torrent_name,
                state=state
            ))

        self._log(f"Found {row_count} row(s) with data-hash attributes", LogLevel.TRACE)

        # Fallback: Look for manage links if no rows found
        if row_count == 0:
            self._log("No data-hash attributes found, trying fallback pattern...", LogLevel.TRACE)
            hash_pattern = r'href="/manage/([a-fA-F0-9]{40})/"'
            hash_matches = re.finditer(hash_pattern, content)
            
            fallback_count = 0
            for match in hash_matches:
                fallback_count += 1
                hash_value = match.group(1).lower()
                
                if hash_value in processed_hashes:
                    continue
                processed_hashes.add(hash_value)

                # Get context around the match
                context_start = max(0, match.start() - 1000)
                context_end = min(len(content), match.end() + 1000)
                context = content[context_start:context_end]

                torrent_name = self._extract_torrent_name(context, hash_value)
                
                self._log(f"  Found {state_name} torrent (fallback): {torrent_name}", LogLevel.TRACE)
                
                torrents.append(TorrentInfo(
                    hash=hash_value,
                    name=torrent_name,
                    state=state
                ))
            
            self._log(f"Fallback: Found {fallback_count} manage link(s)", LogLevel.TRACE)

        self._log(f"Successfully parsed {len(torrents)} {state_name} torrent(s)", LogLevel.DEBUG)
        return torrents

    def _extract_torrent_name(self, content: str, hash_value: str) -> str:
        """Extract torrent name from HTML content"""
        # Pattern 1: Link text
        pattern1 = rf'href="/manage/{hash_value}/">([^<]+)</a>'
        match1 = re.search(pattern1, content)
        if match1:
            name = unescape(match1.group(1).strip())
            self._log(f"Extracted name using pattern 1: {name}", LogLevel.TRACE)
            return name

        # Pattern 2: data-name attribute
        pattern2 = r'data-name="([^"]+)"'
        match2 = re.search(pattern2, content)
        if match2:
            name = unescape(match2.group(1).strip())
            self._log(f"Extracted name using pattern 2: {name}", LogLevel.TRACE)
            return name

        # Pattern 3: First <a> tag
        pattern3 = r'<a[^>]+>([^<]+)</a>'
        match3 = re.search(pattern3, content)
        if match3:
            possible_name = unescape(match3.group(1).strip())
            # Skip if it looks like a size value
            if not re.match(r'^\d+\.\d+\s*(GB|MB|KB|TB)$', possible_name) and len(possible_name) > 5:
                self._log(f"Extracted name using pattern 3: {possible_name}", LogLevel.TRACE)
                return possible_name

        self._log(f"Could not extract name, using default", LogLevel.TRACE)
        return f"Unknown ({hash_value})"

    def get_torrents_by_state(self, state: str) -> Optional[List[TorrentInfo]]:
        """Get torrents by state (broken or under repair)"""
        state_name = "broken" if state == "status_broken" else "under repair"
        
        try:
            self._log(f"Fetching {state_name} torrents from Zurg...", LogLevel.DEBUG)
            url = f"{self.config['zurg_url']}/manage/?state={state}"
            
            self._check_rate_limit()
            content = self._make_request(url)
            
            if content is None:
                self._log(f"Failed to fetch {state_name} torrents page", LogLevel.ERROR, Colors.RED)
                return None

            html_content = content.decode('utf-8', errors='ignore')
            self._log(f"Successfully fetched {state_name} torrents page ({len(html_content)} bytes)", 
                     LogLevel.DEBUG)
            
            torrents = self._parse_torrents_from_html(html_content, state)
            return torrents

        except Exception as e:
            self._log(f"Error getting {state_name} torrents: {str(e)}", LogLevel.ERROR, Colors.RED)
            import traceback
            self._log(f"Stack trace: {traceback.format_exc()}", LogLevel.TRACE)
            return None

    def get_total_torrent_stats(self) -> Optional[Dict[str, int]]:
        """Get total torrent statistics"""
        try:
            self._log("Fetching total torrent statistics...", LogLevel.DEBUG)
            url = f"{self.config['zurg_url']}/manage/"
            
            self._check_rate_limit()
            content = self._make_request(url)
            
            if content is None:
                self._log("Failed to fetch torrents page", LogLevel.ERROR, Colors.RED)
                return None

            html_content = content.decode('utf-8', errors='ignore')
            self._log(f"Successfully fetched torrents page ({len(html_content)} bytes)", LogLevel.DEBUG)

            # Find all unique data-hash attributes
            hash_pattern = r'data-hash="([a-fA-F0-9]{40})"'
            hash_matches = re.finditer(hash_pattern, html_content)
            
            unique_hashes: Set[str] = set()
            for match in hash_matches:
                unique_hashes.add(match.group(1).lower())

            total_torrents = len(unique_hashes)
            self._log(f"Found {total_torrents} total torrent(s)", LogLevel.DEBUG)

            return {"total_torrents": total_torrents}

        except Exception as e:
            self._log(f"Error getting total torrent stats: {str(e)}", LogLevel.ERROR, Colors.RED)
            import traceback
            self._log(f"Stack trace: {traceback.format_exc()}", LogLevel.TRACE)
            return None

    def trigger_repair(self, hash_value: str, name: str) -> bool:
        """Trigger repair for a torrent"""
        try:
            if self.dry_run:
                self._log(f"[DRY RUN] Would trigger repair for: {name}", LogLevel.INFO)
                return True

            self._log(f"Triggering repair for torrent: {name}", LogLevel.INFO, Colors.CYAN)
            repair_url = f"{self.config['zurg_url']}/manage/{hash_value}/repair"
            self._log(f"  Repair URL: {repair_url}", LogLevel.DEBUG)

            self._check_rate_limit()
            content = self._make_request(repair_url, method="POST")

            if content is not None:
                self._log(f"Successfully triggered repair for: {name}", LogLevel.SUCCESS, Colors.GREEN)
                return True
            else:
                self._log(f"Failed to trigger repair for: {name}", LogLevel.ERROR, Colors.RED)
                return False

        except Exception as e:
            self._log(f"Error triggering repair for '{name}': {str(e)}", LogLevel.ERROR, Colors.RED)
            return False

    def perform_check(self):
        """Perform a single check cycle"""
        self._log("", LogLevel.INFO, Colors.CYAN)
        self._log("Starting torrent status check...", LogLevel.INFO, Colors.CYAN)

        # Reset current check stats
        self.stats.current_check = CheckStats()

        # Get total torrent statistics
        total_stats = self.get_total_torrent_stats()
        if total_stats:
            self.stats.current_check.total_torrents = total_stats["total_torrents"]

        # Get broken torrents
        broken_torrents = self.get_torrents_by_state("status_broken")

        # Get under repair torrents
        under_repair_torrents = self.get_torrents_by_state("status_under_repair")

        # Check for API failures
        broken_api_success = broken_torrents is not None
        under_repair_api_success = under_repair_torrents is not None

        # If both API calls failed, that's an error
        if not broken_api_success and not under_repair_api_success:
            self._log("Failed to retrieve torrent status - API calls failed", LogLevel.ERROR, Colors.RED)
            self.stats.total_checks += 1
            self.stats.last_check = datetime.now()
            return

        # Handle API failures gracefully
        if not broken_api_success:
            self._log("Warning: Failed to fetch broken torrents, continuing with under repair check", 
                     LogLevel.WARN, Colors.YELLOW)
            broken_torrents = []

        if not under_repair_api_success:
            self._log("Warning: Failed to fetch under repair torrents, continuing with broken check", 
                     LogLevel.WARN, Colors.YELLOW)
            under_repair_torrents = []

        self.stats.total_checks += 1
        self.stats.last_check = datetime.now()

        # Process broken torrents
        if broken_torrents:
            self.stats.current_check.broken_found = len(broken_torrents)
            self.stats.broken_found += len(broken_torrents)
            
            if len(broken_torrents) > 0:
                self.stats.last_broken_found = datetime.now()

        # Process under repair torrents
        if under_repair_torrents:
            self.stats.current_check.under_repair_found = len(under_repair_torrents)
            self.stats.under_repair_found += len(under_repair_torrents)

        # Calculate OK torrents
        if self.stats.current_check.total_torrents > 0:
            self.stats.current_check.ok_torrents = (
                self.stats.current_check.total_torrents - 
                self.stats.current_check.broken_found - 
                self.stats.current_check.under_repair_found
            )

        self._log(f"Found {self.stats.current_check.broken_found} broken torrent(s)", LogLevel.INFO, Colors.CYAN)
        self._log(f"Found {self.stats.current_check.under_repair_found} under repair torrent(s)", 
                 LogLevel.INFO, Colors.CYAN)

        # Display broken torrents
        if broken_torrents and len(broken_torrents) > 0:
            self._log("", LogLevel.INFO, Colors.CYAN)
            self._log("BROKEN TORRENTS:", LogLevel.WARN, Colors.YELLOW)
            for torrent in broken_torrents:
                self._log(f"  - {torrent.name}", LogLevel.WARN, Colors.YELLOW)
                self.stats.current_check.broken_hashes.append(torrent.hash)
                self.stats.current_check.broken_names.append(torrent.name)

        # Display under repair torrents
        if under_repair_torrents and len(under_repair_torrents) > 0:
            self._log("", LogLevel.INFO, Colors.CYAN)
            self._log("UNDER REPAIR:", LogLevel.INFO, Colors.CYAN)
            for torrent in under_repair_torrents:
                self._log(f"  - {torrent.name}", LogLevel.INFO, Colors.CYAN)
                self.stats.current_check.under_repair_hashes.append(torrent.hash)
                self.stats.current_check.under_repair_names.append(torrent.name)

        # Check if there's anything to repair
        if (not broken_torrents or len(broken_torrents) == 0) and \
           (not under_repair_torrents or len(under_repair_torrents) == 0):
            self._log("", LogLevel.SUCCESS, Colors.GREEN)
            self._log("✓ No broken or under repair torrents found - library is healthy!", 
                     LogLevel.SUCCESS, Colors.GREEN)
            self._log("Torrent status check completed", LogLevel.INFO, Colors.CYAN)
            self.show_check_summary()
            
            # Save current as previous
            self.stats.previous_check_broken = self.stats.current_check.broken_hashes.copy()
            self.stats.previous_check_under_repair = self.stats.current_check.under_repair_hashes.copy()
            self.stats.previous_check_triggered = []
            return

        self._log("", LogLevel.INFO, Colors.CYAN)
        mode_text = "Would trigger" if self.dry_run else "Triggering"
        self._log(f"{mode_text} repairs...", LogLevel.INFO, Colors.CYAN)

        # Trigger repair for broken torrents
        if broken_torrents and len(broken_torrents) > 0:
            for torrent in broken_torrents:
                success = self.trigger_repair(torrent.hash, torrent.name)
                if success:
                    self.stats.current_check.repairs_triggered += 1
                    self.stats.repairs_triggered += 1
                time.sleep(0.5)

        # Trigger repair for under repair torrents (re-trigger)
        if under_repair_torrents and len(under_repair_torrents) > 0:
            self._log("", LogLevel.INFO, Colors.CYAN)
            re_trigger_text = "Would re-trigger" if self.dry_run else "Re-triggering"
            self._log(f"{re_trigger_text} repairs for under repair torrents...", LogLevel.INFO, Colors.CYAN)
            for torrent in under_repair_torrents:
                success = self.trigger_repair(torrent.hash, torrent.name)
                if success:
                    self.stats.current_check.repairs_triggered += 1
                    self.stats.repairs_triggered += 1
                time.sleep(0.5)

        self._log("", LogLevel.INFO, Colors.CYAN)
        self._log("Torrent status check completed", LogLevel.INFO, Colors.CYAN)

        self.show_check_summary()

        # Save current as previous for next check
        self.stats.previous_check_broken = self.stats.current_check.broken_hashes.copy()
        self.stats.previous_check_under_repair = self.stats.current_check.under_repair_hashes.copy()
        self.stats.previous_check_triggered = (
            self.stats.current_check.broken_hashes + 
            self.stats.current_check.under_repair_hashes
        )

    def show_check_summary(self):
        """Display summary of the current check"""
        # Build summary for logging and display
        lines = ["", "=" * 72, "  CHECK SUMMARY", "=" * 72, ""]

        # Log header to file
        for line in lines:
            self._log(line, LogLevel.OUTPUT, Colors.CYAN)
        
        # Display total torrent statistics
        if self.stats.current_check.total_torrents > 0:
            self._log("TORRENT STATISTICS:", LogLevel.OUTPUT, Colors.MAGENTA)
            self._log(f"  Total Torrents:            {self.stats.current_check.total_torrents}", LogLevel.OUTPUT)
            
            # Calculate percentages
            total = self.stats.current_check.total_torrents
            ok_pct = round((self.stats.current_check.ok_torrents / total) * 100, 2) if total > 0 else 0
            broken_pct = round((self.stats.current_check.broken_found / total) * 100, 2) if total > 0 else 0
            repair_pct = round((self.stats.current_check.under_repair_found / total) * 100, 2) if total > 0 else 0

            ok_color = Colors.GREEN
            broken_color = Colors.YELLOW if self.stats.current_check.broken_found > 0 else Colors.GRAY
            repair_color = Colors.CYAN if self.stats.current_check.under_repair_found > 0 else Colors.GRAY

            self._log(f"  OK Torrents:               {self.stats.current_check.ok_torrents} ({ok_pct}%)", LogLevel.OUTPUT, ok_color)
            self._log(f"  Broken:                    {self.stats.current_check.broken_found} ({broken_pct}%)", LogLevel.OUTPUT, broken_color)
            self._log(f"  Under Repair:              {self.stats.current_check.under_repair_found} ({repair_pct}%)", LogLevel.OUTPUT, repair_color)
            self._log("", LogLevel.OUTPUT)


        # Current check results
        broken_color = Colors.YELLOW if self.stats.current_check.broken_found > 0 else Colors.GREEN
        repair_color = Colors.CYAN if self.stats.current_check.under_repair_found > 0 else Colors.GRAY

        self._log("CURRENT CHECK RESULTS:", LogLevel.OUTPUT, Colors.YELLOW)
        self._log(f"  Broken Torrents:           {self.stats.current_check.broken_found}", LogLevel.OUTPUT, broken_color)
        self._log(f"  Under Repair:              {self.stats.current_check.under_repair_found}", LogLevel.OUTPUT, repair_color)
        self._log(f"  Repairs Triggered:         {self.stats.current_check.repairs_triggered}", LogLevel.OUTPUT, Colors.GREEN)        
        
        # Broken torrent list
        if self.stats.current_check.broken_names:
            self._log("", LogLevel.OUTPUT)
            self._log("  Broken Torrents:", LogLevel.OUTPUT, Colors.YELLOW)
            for name in self.stats.current_check.broken_names:
                self._log(f"    - {name}", LogLevel.OUTPUT)                

        # Under repair torrent list
        if self.stats.current_check.under_repair_names:
            self._log("", LogLevel.OUTPUT)
            self._log("  Under Repair:", LogLevel.OUTPUT, Colors.CYAN)
            for name in self.stats.current_check.under_repair_names:
                self._log(f"    - {name}", LogLevel.OUTPUT)

        # Comparison with previous check
        if self.stats.previous_check_triggered:
            self._log("", LogLevel.OUTPUT, Colors.CYAN)
            self._log("COMPARISON WITH PREVIOUS CHECK:", LogLevel.OUTPUT, Colors.CYAN)

            # Calculate metrics
            repaired = sum(1 for h in self.stats.previous_check_triggered 
                          if h not in self.stats.current_check.broken_hashes 
                          and h not in self.stats.current_check.under_repair_hashes)
            
            moved_to_repair = sum(1 for h in self.stats.previous_check_broken 
                                 if h in self.stats.current_check.under_repair_hashes)
            
            still_broken = sum(1 for h in self.stats.previous_check_broken 
                              if h in self.stats.current_check.broken_hashes)
            
            still_under_repair = sum(1 for h in self.stats.previous_check_under_repair 
                                    if h in self.stats.current_check.under_repair_hashes)
            
            new_broken = sum(1 for h in self.stats.current_check.broken_hashes 
                           if h not in self.stats.previous_check_broken 
                           and h not in self.stats.previous_check_under_repair)

            repaired_color = Colors.GREEN if repaired > 0 else Colors.GRAY
            moved_color = Colors.CYAN if moved_to_repair > 0 else Colors.GRAY
            still_broken_color = Colors.YELLOW if still_broken > 0 else Colors.GRAY
            still_repair_color = Colors.CYAN if still_under_repair > 0 else Colors.GRAY
            new_broken_color = Colors.RED if new_broken > 0 else Colors.GRAY

            self._log(f"  Successfully Repaired:     {repaired}", LogLevel.OUTPUT, repair_color)
            self._log(f"  Moved to Repair:           {moved_to_repair}", LogLevel.OUTPUT, moved_color)
            self._log(f"  Still Broken:              {still_broken}", LogLevel.OUTPUT, still_broken_color)
            self._log(f"  Still Under Repair:        {still_under_repair}", LogLevel.OUTPUT, still_repair_color)
            self._log(f"  New Broken:                {new_broken}", LogLevel.OUTPUT, new_broken_color)

            # Calculate success rate
            if len(self.stats.previous_check_triggered) > 0:
                success_rate = round((repaired / len(self.stats.previous_check_triggered)) * 100, 1)

                if success_rate >= 80:
                    rate_color = Colors.GREEN
                elif success_rate >= 50:
                    rate_color = Colors.YELLOW
                else:
                    rate_color = Colors.RED

                self._log(f"  Repair Success Rate:       {success_rate}%", LogLevel.OUTPUT, rate_color)

        # Footer
        self._log("", LogLevel.OUTPUT, Colors.CYAN)
        self._log("=" * 72, LogLevel.OUTPUT, Colors.CYAN)
        self._log("", LogLevel.OUTPUT, Colors.CYAN)

    def show_overall_statistics(self):
        """Display overall statistics"""
        # Log banner
        line = "=" * 72
        self._log("", LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(line, LogLevel.OUTPUT, Colors.MAGENTA)
        self._log("  OVERALL STATISTICS", LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(line, LogLevel.OUTPUT, Colors.MAGENTA)
        self._log("", LogLevel.OUTPUT, Colors.MAGENTA)

        last_check = self.stats.last_check.strftime("%Y-%m-%d %H:%M:%S") if self.stats.last_check else "Never"
        last_broken = self.stats.last_broken_found.strftime("%Y-%m-%d %H:%M:%S") if self.stats.last_broken_found else "Never"

        # Log to file
        self._log(f"Total Checks Performed:    {self.stats.total_checks}", LogLevel.OUTPUT, Colors.CYAN)
        self._log(f"Total Broken Found:        {self.stats.broken_found}", LogLevel.OUTPUT, Colors.CYAN)
        self._log(f"Total Under Repair Found:  {self.stats.under_repair_found}", LogLevel.OUTPUT, Colors.CYAN)
        self._log(f"Total Repairs Triggered:   {self.stats.repairs_triggered}", LogLevel.OUTPUT, Colors.CYAN)
        self._log(f"Last Check:                {last_check}", LogLevel.OUTPUT, Colors.CYAN)
        self._log(f"Last Broken Found:         {last_broken}", LogLevel.OUTPUT, Colors.CYAN)
        self._log("", LogLevel.OUTPUT, Colors.MAGENTA)
        self._log(line, LogLevel.OUTPUT, Colors.MAGENTA)

    def run_once(self):
        """Run a single check"""
        self._log_banner(f"{SCRIPT_NAME} v{VERSION}")
        
        self._log(f"Starting {SCRIPT_NAME}", LogLevel.INFO, Colors.CYAN)
        self._log(f"Zurg URL: {self.config['zurg_url']}", LogLevel.INFO, Colors.CYAN)
        self._log(f"Log File: {self.config['log_file']}", LogLevel.INFO, Colors.CYAN)
        auth_status = "Enabled" if self.config.get('username') else "Disabled"
        self._log(f"Authentication: {auth_status}", LogLevel.INFO, Colors.CYAN)
        if self.dry_run:
            self._log("DRY RUN MODE: No repairs will be triggered", LogLevel.WARN, Colors.YELLOW)
        self._log("", LogLevel.INFO)

        if not self.test_connection():
            self._log("Cannot connect to Zurg - exiting", LogLevel.ERROR, Colors.RED)
            return 1

        self._log("", LogLevel.OUTPUT)
        self._log("Running in single-check mode", LogLevel.INFO, Colors.CYAN)
        
        self.perform_check()
        
        self._log("", LogLevel.OUTPUT)
        self.show_overall_statistics()
        return 0

    def run_continuous(self):
        """Run continuous monitoring loop"""
        self._log_banner(f"{SCRIPT_NAME} v{VERSION}")
        
        self._log(f"Starting {SCRIPT_NAME}", LogLevel.INFO, Colors.CYAN)
        self._log(f"Zurg URL: {self.config['zurg_url']}", LogLevel.INFO, Colors.CYAN)
        self._log(f"Check Interval: {self.config['check_interval']} minutes", LogLevel.INFO, Colors.CYAN)
        self._log(f"Log File: {self.config['log_file']}", LogLevel.INFO, Colors.CYAN)
        auth_status = "Enabled" if self.config.get('username') else "Disabled"
        self._log(f"Authentication: {auth_status}", LogLevel.INFO, Colors.CYAN)
        if self.dry_run:
            self._log("DRY RUN MODE: No repairs will be triggered", LogLevel.WARN, Colors.YELLOW)
        self._log("", LogLevel.INFO, Colors.CYAN)

        if not self.test_connection():
            self._log("Cannot connect to Zurg - exiting", LogLevel.ERROR, Colors.RED)
            return 1

        self._log("", LogLevel.OUTPUT)
        self._log("Starting continuous monitoring loop (press Ctrl+C to stop)", LogLevel.OUTPUT)
        self._log("", LogLevel.OUTPUT)

        try:
            while True:
                self.perform_check()
                
                self._log("", LogLevel.OUTPUT)
                self._log(f"Next check in {self.config['check_interval']} minutes...", LogLevel.OUTPUT)
                self._log("=" * 72, LogLevel.OUTPUT)
                self._log("", LogLevel.OUTPUT)
                
                time.sleep(self.config['check_interval'] * 60)

        except KeyboardInterrupt:
            self._log("", LogLevel.WARN, Colors.YELLOW)
            self._log("Monitoring loop interrupted by user", LogLevel.WARN, Colors.YELLOW)
        except Exception as e:
            self._log(f"Monitoring loop interrupted: {str(e)}", LogLevel.WARN, Colors.YELLOW)
        finally:
            self._log("", LogLevel.OUTPUT)
            self.show_overall_statistics()
            self._log("Monitoring stopped", LogLevelOUTPUT)
            return 0


def load_config(args: argparse.Namespace) -> Dict:
    """Load configuration from file and merge with CLI arguments"""
    # Get script directory
    script_dir = Path(__file__).parent.resolve()
    
    config = {
        'zurg_url': 'http://localhost:9999',
        'username': '',
        'password': '',
        'check_interval': 30,
        'log_file': str(script_dir / 'logs' / 'zurg-monitor.log'),
        'rate_limit_requests': 10,
        'rate_limit_delay': 0.5,
        'rate_limit_backoff': 5,
        'verbose': False,
    }

    # Try to find config file
    config_paths = [
        Path(args.config) if args.config else None,
        Path('./zurg-monitor.conf'),
        Path.home() / '.config' / 'zurg-monitor' / 'zurg-monitor.conf',
        Path('/etc/zurg-monitor/zurg-monitor.conf'),
    ]

    config_file = None
    for path in config_paths:
        if path and path.exists():
            config_file = path
            break

    # Load from config file if found
    if config_file:
        print(f"Loading configuration from: {config_file}")
        parser = configparser.ConfigParser()
        parser.read(config_file)

        if 'zurg' in parser:
            section = parser['zurg']
            config['zurg_url'] = section.get('zurg_url', config['zurg_url'])
            config['username'] = section.get('username', config['username'])
            config['password'] = section.get('password', config['password'])
            config['check_interval'] = section.getint('check_interval', config['check_interval'])
            config['log_file'] = section.get('log_file', config['log_file'])
            config['rate_limit_requests'] = section.getint('rate_limit', config['rate_limit_requests'])
            config['rate_limit_delay'] = section.getfloat('rate_limit_delay', config['rate_limit_delay'])
            config['rate_limit_backoff'] = section.getfloat('rate_limit_backoff', config['rate_limit_backoff'])
            config['verbose'] = section.getboolean('verbose', config['verbose'])
    else:
        print("No configuration file found, using defaults")

    # CLI arguments override config file
    if args.zurg_url:
        config['zurg_url'] = args.zurg_url
    if args.username:
        config['username'] = args.username
    if args.password:
        config['password'] = args.password
    if args.check_interval:
        config['check_interval'] = args.check_interval
    if args.log_file:
        config['log_file'] = args.log_file
    if args.rate_limit:
        config['rate_limit_requests'] = args.rate_limit
    if args.verbose:
        config['verbose'] = True

    # Add verbosity flags
    config['trace'] = args.trace
    config['debug'] = args.debug or args.trace  # Trace implies debug

    return config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=f'{SCRIPT_NAME} v{VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once with default config
  %(prog)s --run-once
  
  # Run continuously with custom interval
  %(prog)s --check-interval 60
  
  # Run with custom Zurg URL
  %(prog)s --zurg-url http://192.168.1.100:9999
  
  # Dry run to see what would happen
  %(prog)s --run-once --dry-run
  
  # Enable verbose logging
  %(prog)s --run-once --verbose
  
  # Enable debug logging
  %(prog)s --run-once --debug
  
  # Enable trace logging (very verbose)
  %(prog)s --run-once --trace
        """
    )

    parser.add_argument('-c', '--config',
                       help='Path to configuration file (default: search standard locations)')
    parser.add_argument('-u', '--zurg-url',
                       help='Zurg URL (default: http://localhost:9999)')
    parser.add_argument('--username',
                       help='Username for authentication')
    parser.add_argument('--password',
                       help='Password for authentication')
    parser.add_argument('-i', '--check-interval',
                       type=int,
                       help='Check interval in minutes (default: 30)')
    parser.add_argument('-l', '--log-file',
                       help='Log file path (default: ./logs/zurg-monitor.log)')
    parser.add_argument('--run-once',
                       action='store_true',
                       help='Run a single check and exit')
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Enable verbose logging (show INFO messages)')
    parser.add_argument('-t', '--trace',
                       action='store_true',
                       help='Enable trace logging (very verbose)')
    parser.add_argument('-d', '--debug',
                       action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be done without triggering repairs')
    parser.add_argument('-r', '--rate-limit',
                       type=int,
                       help='Number of requests before backing off (default: 10)')
    parser.add_argument('--version',
                       action='version',
                       version=f'{SCRIPT_NAME} v{VERSION}')

    args = parser.parse_args()

    # Validate check interval
    if args.check_interval and args.check_interval < 1:
        print("Error: Check interval must be at least 1 minute")
        return 1

    # Load configuration
    config = load_config(args)

    # Create monitor instance
    monitor = ZurgMonitor(config, dry_run=args.dry_run)

    # Run
    if args.run_once:
        return monitor.run_once()
    else:
        return monitor.run_continuous()


if __name__ == '__main__':
    sys.exit(main())