import requests

# Test logging in as the rejected college FH (ALTS)
url = "http://localhost:8000/api/login"
try:
    # First, let's try the login endpoint without /api if that fails
    resp = requests.post("http://localhost:8000/api/auth/login", json={"userId": "FH", "password": "DEBUGME"})
    if resp.status_code == 404:
        resp = requests.post("http://localhost:8000/login", json={"userId": "FH", "password": "DEBUGME"})
        
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Server not running: {e}")
