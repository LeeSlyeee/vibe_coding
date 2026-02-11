#!/bin/bash
cd /home/ubuntu/project/backend
pkill -f app.py
sleep 2
nohup .venv/bin/python -u app.py > /home/ubuntu/debug.log 2>&1 &
echo "Started app.py, see /home/ubuntu/debug.log"
