#!/bin/bash
export PATH=/home/ubuntu/.nvm/versions/node/v20.20.0/bin:$PATH
cd /home/ubuntu/project/temp_insight_deploy/frontend
# Kill existing vite on port 3000
fuser -k 3000/tcp || true
nohup npm run dev -- --host --port 3000 > staff_frontend.log 2>&1 &
echo "Started Staff Frontend with PID $!"
