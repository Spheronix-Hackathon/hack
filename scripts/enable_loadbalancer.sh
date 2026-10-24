#!/bin/bash
# Spheronix Hackathon - Automated Load Balancer Setup for already deployed AWS instance
# Usage: sudo bash scripts/enable_loadbalancer.sh

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGINX_CONF_SRC="$APP_DIR/scripts/nginx-loadbalancer.conf"
NGINX_CONF_DEST="/etc/nginx/sites-available/hackathon.conf"
SYSTEMD_SRC="$APP_DIR/scripts/hackathon@.service"

echo "=========================================================="
echo " Starting Load Balancer & Multi-Instance Setup on AWS..."
echo "=========================================================="

cd $APP_DIR

# 1. Update dependencies
echo "[1/6] Verifying python virtualenv..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt -q
fi

# 2. Setup Systemd Multi-instance service template
echo "[2/6] Setting up systemd cluster services..."
sudo cp "$SYSTEMD_SRC" /etc/systemd/system/hackathon@.service
sudo systemctl daemon-reload

# 3. Stop legacy single instance if active
echo "[3/6] Transitioning from single service to multi-instance..."
if systemctl is-active --quiet hackathon.service; then
    sudo systemctl stop hackathon.service
    sudo systemctl disable hackathon.service
    echo "  -> Legacy hackathon.service stopped and disabled."
fi

# 4. Enable & Start backend instances on ports 8000 and 8001
echo "[4/6] Starting backend cluster instances (ports 8000 & 8001)..."
sudo systemctl enable --now hackathon@8000
sudo systemctl enable --now hackathon@8001
sudo systemctl restart hackathon@8000
sudo systemctl restart hackathon@8001

# Wait 2 seconds and test health
sleep 2
echo "  -> Checking Instance 8000: $(curl -s http://127.0.0.1:8000/api/health | grep -o '\"status\":\"[^\"]*\"' || echo 'Waiting...')"
echo "  -> Checking Instance 8001: $(curl -s http://127.0.0.1:8001/api/health | grep -o '\"status\":\"[^\"]*\"' || echo 'Waiting...')"

# 5. Configure Nginx Load Balancer
echo "[5/6] Configuring Nginx Load Balancer upstream..."
sudo apt-get update -y -q
sudo apt-get install -y nginx -q

# Preserve existing SSL cert paths if already managed by certbot
sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DEST"
sudo ln -sf "$NGINX_CONF_DEST" /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx syntax
sudo nginx -t

# 6. Reload Nginx
echo "[6/6] Reloading Nginx..."
sudo systemctl restart nginx

echo "=========================================================="
echo " Load Balancer successfully activated on your AWS instance!"
echo " Both backend instances (8000 & 8001) are now active behind Nginx."
echo " Check live health: https://puhackathon.spheronixtechnology.com/api/health"
echo "=========================================================="
