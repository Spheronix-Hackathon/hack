#!/bin/bash
# Start 2 production Gunicorn instances on Linux for Load Balancer

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Backend Instance 1 on Port 8000..."
SERVER_PORT=8000 gunicorn -c gunicorn_conf.py app.main:app &

echo "Starting Backend Instance 2 on Port 8001..."
SERVER_PORT=8001 gunicorn -c gunicorn_conf.py app.main:app &

echo "Both instances running in background."
echo "Instance 1 -> http://127.0.0.1:8000"
echo "Instance 2 -> http://127.0.0.1:8001"
echo "Check health: curl http://127.0.0.1:8000/api/health"
