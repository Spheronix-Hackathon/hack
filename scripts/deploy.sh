#!/bin/bash

# Deployment Script for Spheronix Hackathon API
# Usage: ./scripts/deploy.sh

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="hackathon.service"

echo "Starting deployment..."

cd $APP_DIR

# Pull latest changes from git (assuming ssh keys are set up)
echo "Pulling latest changes..."
git pull origin main

# Update virtual environment
echo "Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Restart systemd services (Cluster or single instance)
echo "Restarting services..."
if systemctl is-active --quiet hackathon@8000; then
    sudo systemctl restart hackathon@8000 hackathon@8001
    sudo systemctl reload nginx
    echo "Cluster instances (8000 & 8001) and Nginx reloaded."
else
    sudo systemctl restart $SERVICE_NAME
fi

# Check status
echo "Checking service status..."
if systemctl is-active --quiet hackathon@8000; then
    sudo systemctl status hackathon@8000 hackathon@8001 --no-pager
else
    sudo systemctl status $SERVICE_NAME --no-pager
fi

echo "Deployment complete!"
