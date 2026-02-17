#!/bin/bash
pkill -f 'app.py' || true
sleep 2
cd /home/ubuntu/project/backend
export DATABASE_URL='postgresql://vibe_user:vibe1234@127.0.0.1/vibe_db'
nohup venv/bin/python -u app.py > /home/ubuntu/app.log 2>&1 < /dev/null &
echo "Backed Server Started with PID: $!"
exit 0
