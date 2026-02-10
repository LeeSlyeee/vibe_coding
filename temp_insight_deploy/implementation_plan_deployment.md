# Implementation Plan - OCI Deployment

This plan outlines the steps to fully deploy the InsightMind stack to the OCI instance.

## Current Status

- **Codebase**: Uploaded to `~/InsightMind`.
- **Python Env**: `venv` created, dependencies installed (versions relaxed for Python 3.8 compat).
- **Missing Components**: MariaDB, Node.js, Nginx.

## Proposed Steps

### 1. Database Setup (MariaDB)

- **Install**: `sudo apt install mariadb-server`
- **Configure**:
  - Secure installation (root password).
  - Create database `maumon_db`.
  - Create user (or use root as per current dev config, though explicit user is safer).
  - Update `.env` on server if needed.

### 2. Frontend Setup (Node.js)

- **Install NVM**: Install Node Version Manager.
- **Install Node**: Install generic LTS (v20) or v18.
- **Build**: Run `npm install && npm run build` in `frontend/`.

### 3. Web Server & Proxy (Nginx)

- **Install**: `sudo apt install nginx`
- **Config**: Create `/etc/nginx/sites-available/insightmind` to:
  - Serve `frontend/dist`.
  - Proxy `/api` to Gunicorn/Django (port 8000 or unix socket).
- **SSL**: Certbot for HTTPS (if domain is available, otherwise HTTP for IP).

### 4. Process Management (Systemd)

- **Gunicorn**: Create `insightmind.service` to keep Django running.
- **Nginx**: Enable on boot.

## User Action Required

- **Confirm**: Should I proceed with installing MariaDB, Node.js, and Nginx?
- **Conflict**: A Python HTTP server is running on port 8000 (PID 2399). Should this be stopped?
