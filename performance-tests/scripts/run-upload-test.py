import jwt
import datetime
import os
import subprocess

JWT_SECRET = "spheronix-hackathon-super-secret-key"
payload = {
    "userId": "TEST_USER_123",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print(f"Generated test JWT: {token}")

env = os.environ.copy()
env["K6_JWT"] = token

subprocess.run(["C:\\Program Files\\k6\\k6.exe", "run", "performance-tests/scenarios/upload.js", "--summary-export=performance-tests/results/upload-summary.json"], env=env)
