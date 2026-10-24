import multiprocessing
import os

# Server socket (Supports running multiple instances behind a load balancer)
_host = os.getenv("SERVER_HOST", "127.0.0.1")
_port = os.getenv("SERVER_PORT", "8000")
bind = os.getenv("GUNICORN_BIND", f"{_host}:{_port}")
backlog = 2048

# Worker processes
# For async FastAPI behind a load balancer, 2-4 workers per instance is optimal.
_default_workers = min(4, multiprocessing.cpu_count() * 2 + 1)
workers = int(os.getenv("GUNICORN_WORKERS", _default_workers))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 2

# Forwarded headers from Load Balancer / Reverse Proxy
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1,::1")

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = f"hackathon_api_{_port}"
