# Start 2 backend instances locally for load balancer testing
Write-Host "Starting Spheronix Hackathon Cluster..." -ForegroundColor Cyan

# Start Instance 1 on Port 8000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:SERVER_PORT='8000'; uvicorn app.main:app --host 127.0.0.1 --port 8000"

# Start Instance 2 on Port 8001
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:SERVER_PORT='8001'; uvicorn app.main:app --host 127.0.0.1 --port 8001"

Write-Host "Instances started:" -ForegroundColor Green
Write-Host "  Instance 1: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "  Instance 2: http://127.0.0.1:8001" -ForegroundColor Yellow
Write-Host "Point your load balancer upstream to 127.0.0.1:8000 and 127.0.0.1:8001." -ForegroundColor Green
