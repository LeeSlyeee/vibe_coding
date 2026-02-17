#!/bin/bash
# Standard Gunicorn Startup Script
# Should be resilient and log output

# 1. Kill old processes
echo "Stopping existing Gunicorn..."
pkill -f 'gunicorn' || true
sleep 3

# 2. Navigate to project root
cd /home/ubuntu/project/temp_insight_deploy/backend

# 3. Start Gunicorn with robust settings
# - bind: 0.0.0.0:8000 (standard port)
# - workers: 3
# - timeout: 120 (prevent timeouts)
# - access/error log: distinct files
# - capture-output: true (capture stdout/stderr)
echo "Starting Gunicorn..."
nohup venv/bin/gunicorn --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile django_access.log \
    --error-logfile django_error.log \
    --capture-output \
    --log-level debug \
    config.wsgi:application > /dev/null 2>&1 &

echo "Django Gunicorn Started (PID: $!)"
exit 0
