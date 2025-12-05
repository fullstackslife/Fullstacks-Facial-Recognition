#!/usr/bin/env python3
"""Railway startup script that properly handles PORT environment variable"""
import os
import subprocess
import sys

# Get PORT from environment (Railway sets this automatically)
port = os.environ.get('PORT', '8080')

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
sys.exit(subprocess.run(cmd).returncode)

