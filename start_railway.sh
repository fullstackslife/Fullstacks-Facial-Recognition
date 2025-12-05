#!/bin/bash
# Railway startup script
# Read PORT from environment
PORT="${PORT:-8080}"

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: Invalid PORT value: '$PORT'"
    echo "PORT must be a number, got: $(echo "$PORT" | head -c 50)"
    exit 1
fi

# Validate port range
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "ERROR: PORT out of range: $PORT (must be 1-65535)"
    exit 1
fi

echo "Starting gunicorn on port $PORT"
exec gunicorn app:app --bind "0.0.0.0:${PORT}" --workers 2 --threads 2 --timeout 120

