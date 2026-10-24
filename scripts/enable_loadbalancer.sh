#!/bin/bash
# Spheronix Hackathon - Automated Load Balancer & High Concurrency Cluster Setup
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGINX_CONF_SRC="$APP_DIR/scripts/nginx-loadbalancer.conf"
NGINX_CONF_DEST="/etc/nginx/sites-available/hackathon.conf"
SYSTEMD_SRC="$APP_DIR/scripts/hackathon@.service"

echo "=========================================================="
echo " Starting Load Balancer & Multi-Instance Setup on AWS..."
echo " Directory: $APP_DIR"
echo "=========================================================="

cd "$APP_DIR"

# Ensure .env and venv exist in repo root
if [ ! -f ".env" ] && [ -f "hackathon registration/.env" ]; then
    echo "Copying .env from hackathon registration..."
    cp "hackathon registration/.env" .env
fi

if [ ! -d "venv" ] && [ -d "hackathon registration/venv" ]; then
    echo "Copying venv from hackathon registration..."
    cp -a "hackathon registration/venv" venv
fi

# 1. Make all helper scripts executable
chmod +x "$APP_DIR/scripts/"*.sh 2>/dev/null || true

# 2. Update python environment
echo "[1/5] Verifying python virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt -q
fi

# 3. Setup systemd template
echo "[2/5] Setting up systemd cluster services..."
sudo cp "$SYSTEMD_SRC" /etc/systemd/system/hackathon@.service
sudo systemctl daemon-reload

# 4. Stop legacy single instance if running
echo "[3/5] Transitioning to 2-instance cluster (ports 8000 & 8001)..."
sudo systemctl stop hackathon.service 2>/dev/null || true
sudo systemctl disable hackathon.service 2>/dev/null || true
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8001/tcp 2>/dev/null || true
sleep 1

# Start cluster instances
sudo systemctl enable hackathon@8000 hackathon@8001
sudo systemctl restart hackathon@8000 hackathon@8001

echo "Waiting for backend instances to initialize..."
sleep 3

# 5. Check backend instances
echo "[4/5] Testing backend health..."
HEALTH_8000=$(curl -s http://127.0.0.1:8000/api/health || echo "FAILED")
HEALTH_8001=$(curl -s http://127.0.0.1:8001/api/health || echo "FAILED")
echo "  -> Port 8000: $HEALTH_8000"
echo "  -> Port 8001: $HEALTH_8001"

# 6. Configure Nginx Load Balancer
echo "[5/5] Configuring and restarting Nginx Load Balancer..."
sudo apt-get update -y -q
sudo apt-get install -y nginx -q

sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DEST"
sudo ln -sf "$NGINX_CONF_DEST" /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl restart nginx

echo "=========================================================="
echo " SUCCESS! Load Balancer is active."
echo " Domain: studentregistration.spheronixtechnology.in"
echo " Backend Instances: 127.0.0.1:8000 & 127.0.0.1:8001"
echo " Waiting Room: http://studentregistration.spheronixtechnology.in/waiting-room.html"
echo "=========================================================="
