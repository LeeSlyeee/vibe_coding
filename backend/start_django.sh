#!/bin/bash
# start_django.sh - Production-ready Django Server Script
# Created: 2026-02-15
# Description: Starts Django server on port 8000 (bind to 0.0.0.0)

# Environment Setup
export DB_NAME=reboot_db
export DB_USER=maumON_admin
export DB_PASSWORD=maumON_1234
export DB_HOST=127.0.0.1
export DB_PORT=5432
export SECRET_KEY=django-insecure-key-for-dev
export DEBUG=True

# Kill any existing Django process on port 8000
echo "🛑 Killing existing Django process..."
kill -9 $(lsof -t -i:8000) 2>/dev/null

# Get Script Directory and Move to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ Warning: venv folder not found in $SCRIPT_DIR"
fi

# Run Django Server
echo "🚀 Starting Django Server on 0.0.0.0:8000..."
nohup gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile django_access.log \
  --error-logfile django_error.log \
  --capture-output \
  --log-level debug \
  config.wsgi:application > django_full.log 2>&1 &
echo "Django Started via Wrapper Script (PID: $!) using $DB_USER"
