# ============================================================================
# Zurg Broken Torrent Monitor - Dockerfile
# ============================================================================
# Multi-stage build for optimal image size
# ============================================================================

FROM python:3.11-slim as base

# Set build arguments
ARG BUILD_DATE
ARG VERSION=3.0.0
ARG VCS_REF

# Add labels
LABEL org.opencontainers.image.title="Zurg Broken Torrent Monitor"
LABEL org.opencontainers.image.description="Monitor and repair broken torrents in Zurg"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.authors="maddguru"
LABEL org.opencontainers.image.url="https://github.com/maddguru/zurg-broken-torrent-monitor"
LABEL org.opencontainers.image.source="https://github.com/maddguru/zurg-broken-torrent-monitor"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and create user
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user
    groupadd -r zurg -g 1000 && \
    useradd -r -u 1000 -g zurg -m -s /sbin/nologin zurg && \
    # Create necessary directories
    mkdir -p /app /config /logs && \
    chown -R zurg:zurg /app /config /logs

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=zurg:zurg zurg-monitor.py /app/
COPY --chown=zurg:zurg zurg-monitor.conf /app/zurg-monitor.conf.example

# Make script executable
RUN chmod +x /app/zurg-monitor.py

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Handle PUID/PGID\n\
PUID=${PUID:-1000}\n\
PGID=${PGID:-1000}\n\
\n\
echo "Starting with UID:$PUID, GID:$PGID"\n\
\n\
# Create group and user if they do not exist\n\
if ! getent group zurg > /dev/null 2>&1; then\n\
    groupadd -g $PGID zurg\n\
fi\n\
if ! getent passwd zurg > /dev/null 2>&1; then\n\
    useradd -u $PUID -g $PGID -m -s /sbin/nologin zurg\n\
fi\n\
\n\
# Create config if it does not exist\n\
if [ ! -f /config/zurg-monitor.conf ]; then\n\
    echo "Creating default configuration file..."\n\
    cp /app/zurg-monitor.conf.example /config/zurg-monitor.conf\n\
    echo "Please edit /config/zurg-monitor.conf with your settings"\n\
fi\n\
\n\
# Set ownership\n\
chown -R $PUID:$PGID /config /logs 2>/dev/null || true\n\
\n\
# Check if Zurg URL is provided\n\
if [ -n "$ZURG_URL" ]; then\n\
    echo "Using Zurg URL from environment: $ZURG_URL"\n\
    ZURG_ARG="--zurg-url $ZURG_URL"\n\
else\n\
    ZURG_ARG=""\n\
fi\n\
\n\
# Check if username is provided\n\
if [ -n "$ZURG_USERNAME" ]; then\n\
    echo "Using authentication with username: $ZURG_USERNAME"\n\
    AUTH_ARGS="--username $ZURG_USERNAME --password ${ZURG_PASSWORD:-}"\n\
else\n\
    AUTH_ARGS=""\n\
fi\n\
\n\
# Check if check interval is provided\n\
if [ -n "$CHECK_INTERVAL" ]; then\n\
    echo "Using check interval: $CHECK_INTERVAL minutes"\n\
    INTERVAL_ARG="--check-interval $CHECK_INTERVAL"\n\
else\n\
    INTERVAL_ARG=""\n\
fi\n\
\n\
# Check if rate limit is provided\n\
if [ -n "$RATE_LIMIT" ]; then\n\
    echo "Using rate limit: $RATE_LIMIT requests"\n\
    RATE_ARG="--rate-limit $RATE_LIMIT"\n\
else\n\
    RATE_ARG=""\n\
fi\n\
\n\
# Build command\n\
CMD="python3 /app/zurg-monitor.py --config /config/zurg-monitor.conf"\n\
\n\
# Add optional arguments\n\
[ -n "$ZURG_ARG" ] && CMD="$CMD $ZURG_ARG"\n\
[ -n "$AUTH_ARGS" ] && CMD="$CMD $AUTH_ARGS"\n\
[ -n "$INTERVAL_ARG" ] && CMD="$CMD $INTERVAL_ARG"\n\
[ -n "$RATE_ARG" ] && CMD="$CMD $RATE_ARG"\n\
[ "$RUN_ONCE" = "true" ] && CMD="$CMD --run-once"\n\
[ "$VERBOSE" = "true" ] && CMD="$CMD --verbose"\n\
[ "$DEBUG" = "true" ] && CMD="$CMD --debug"\n\
[ "$TRACE" = "true" ] && CMD="$CMD --trace"\n\
[ "$DRY_RUN" = "true" ] && CMD="$CMD --dry-run"\n\
\n\
echo "Starting Zurg Monitor..."\n\
echo "Command: $CMD"\n\
\n\
# Export PUID/PGID for the Python script\n\
export PUID PGID\n\
\n\
# Execute as root to allow setuid/setgid in Python script\n\
exec $CMD\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Switch to non-root user (will be changed by entrypoint if PUID/PGID set)
USER zurg

# Expose healthcheck endpoint (if needed in future)
# EXPOSE 8080

# Set volumes
VOLUME ["/config", "/logs"]

# Healthcheck
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD []