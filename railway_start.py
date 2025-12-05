#!/usr/bin/env python3
"""Railway startup script that properly handles PORT environment variable"""
import os
import subprocess
import sys

# Get PORT from environment (Railway sets this automatically)
port = os.environ.get('PORT')
if not port:
    print("WARNING: PORT environment variable not set, using default 8080")
    port = '8080'

# Validate port is a number
try:
    port_int = int(port)
    if port_int < 1 or port_int > 65535:
        raise ValueError(f"Port {port_int} is out of range")
except ValueError as e:
    print(f"ERROR: Invalid PORT value '{port}': {e}")
    sys.exit(1)

print(f"Starting gunicorn on port {port}")

# Build gunicorn command
cmd = [
    'gunicorn',
    'app:app',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '2',
    '--threads', '2',
    '--timeout', '120'
]

# Execute gunicorn
try:
    sys.exit(subprocess.run(cmd).returncode)
except FileNotFoundError:
    print("ERROR: gunicorn not found. Make sure it's installed in requirements.txt")
    sys.exit(1)

