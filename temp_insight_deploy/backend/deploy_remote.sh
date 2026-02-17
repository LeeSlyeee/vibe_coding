#!/bin/bash

# 0. System Setup
echo "--- Installing System Dependencies ---"
sudo apt-get update
sudo apt-get install -y unzip python3-pip python3-venv libpq-dev postgresql-client

# 1. Setup Database
echo "--- Setting up Database ---"
sudo -u postgres psql -c "CREATE USER slyeee WITH SUPERUSER PASSWORD 'vibe1234';" || echo "User slyeee might exist"
sudo -u postgres psql -c "ALTER USER slyeee WITH SUPERUSER;"
# Drop existing DB to ensure clean state
sudo -u postgres psql -c "DROP DATABASE IF EXISTS reboot_db;"
sudo -u postgres psql -c "CREATE DATABASE reboot_db OWNER slyeee;"

# 2. Restore Dump
echo "--- Restoring Data ---"
PGPASSWORD=vibe1234 psql -h localhost -U slyeee -d reboot_db -f reboot_db_dump.sql || echo "Restore warnings (ignored)"

# 3. Setup Backend Code
echo "--- Deploying Code ---"
rm -rf backend_new
mkdir -p backend_new
unzip -o backend_deploy.zip -d backend_new
cd backend_new

# 4. Setup Python Environment
echo "--- Setting up Python Venv ---"
python3 -m venv venv
source venv/bin/activate

# 5. Install Requirements
echo "--- Installing Python Dependencies ---"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
pip install gunicorn psycopg2-binary django-cors-headers djangorestframework django # Ensure critical deps

# 6. Start Application
echo "--- Starting Server ---"
# Kill old Gunicorn
pkill gunicorn || true

# Bind to 0.0.0.0:8000
nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 --log-level debug > server.log 2>&1 &

echo "Deployment Complete. Server running on port 8000."
echo "Check server.log for details."
