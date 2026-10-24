#!/bin/bash
# Spheronix Hackathon - Instance runner for systemd
PORT=${1:-8000}
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

export SERVER_PORT="$PORT"
export GUNICORN_BIND="127.0.0.1:$PORT"

exec gunicorn -c gunicorn_conf.py app.main:app
