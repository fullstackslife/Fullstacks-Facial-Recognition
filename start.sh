#!/bin/bash

# Face Detection & Analysis System - Startup Script
# This script helps start the application with proper configuration

echo "🎥 Starting Face Detection & Analysis System..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import cv2, flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies are missing. Installing..."
    pip3 install -r requirements.txt
fi

# Get port from environment or use default
PORT=${PORT:-8080}
HOST=${HOST:-0.0.0.0}

echo "🚀 Starting server on http://${HOST}:${PORT}"
echo "📱 Open your browser and navigate to: http://localhost:${PORT}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 app.py


