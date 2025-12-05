#!/usr/bin/env python3
"""Railway startup script that properly handles PORT environment variable"""
import os
import subprocess
import sys

# Debug: Print all environment variables that might be relevant
print("=== Railway Startup Debug ===")
print(f"PORT env var: {repr(os.environ.get('PORT'))}")
print(f"All env vars with PORT: {[k for k in os.environ.keys() if 'PORT' in k.upper()]}")

# Get PORT from environment (Railway sets this automatically)
port = os.environ.get('PORT')
if not port:
    print("WARNING: PORT environment variable not set, using default 8080")
    port = '8080'
else:
    print(f"Found PORT environment variable: {port}")

# Validate port is a number
try:
    port_int = int(port)
    if port_int < 1 or port_int > 65535:
        raise ValueError(f"Port {port_int} is out of range")
    print(f"Validated port: {port_int}")
except ValueError as e:
    print(f"ERROR: Invalid PORT value '{port}': {e}")
    print(f"PORT type: {type(port)}, PORT repr: {repr(port)}")
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

print(f"Executing command: {' '.join(cmd)}")

# Execute gunicorn
try:
    result = subprocess.run(cmd, check=False)
    print(f"Gunicorn exited with code: {result.returncode}")
    sys.exit(result.returncode)
except FileNotFoundError as e:
    print(f"ERROR: gunicorn not found: {e}")
    print("Make sure it's installed in requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

