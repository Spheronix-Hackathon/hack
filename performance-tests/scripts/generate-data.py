import json
import random
import string
import pandas as pd
import os

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_test_data(num_users=100):
    users = []
    for i in range(num_users):
        user = {
            "collegeCode": f"CCODE{i}{generate_random_string(4)}",
            "principalName": f"Principal {i}",
            "principalEmail": f"principal{i}@test.com",
            "principalMobile": f"9000000{i:03d}"[:10],
            "nodalOfficerName": f"Nodal {i}",
            "nodalOfficerEmail": f"nodal{i}@test.com",
            "nodalOfficerMobile": f"8000000{i:03d}"[:10],
            "password": "Password123!",
            "confirmPassword": "Password123!"
        }
        users.append(user)
    
    os.makedirs("performance-tests/data", exist_ok=True)
    with open("performance-tests/data/test-users.json", "w") as f:
        json.dump(users, f, indent=4)
        
    print(f"Generated {num_users} test users in performance-tests/data/test-users.json")

def generate_test_excel(rows=100, filename="performance-tests/data/test-upload.xlsx"):
    data = []
    for i in range(rows):
        row = {
            "S.No": i + 1,
            "Roll Number": f"ROLL{i}",
            "Full Name": f"Student {i}",
            "Current Year": random.choice(["2nd Year", "3rd Year", "4th Year"]),
            "Branch": "CSE",
            "College Name": "Test College",
            "Gmail Address": f"student{i}@test.com",
            "Mobile Number": f"7000000{i:03d}"[:10],
            "Select Domain (Drop Down)": random.choice(["Web Development", "App Development"]),
            "Mode (Drop Down)": "Individual",
            "Team Name": ""
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Generated test excel with {rows} rows at {filename}")

if __name__ == "__main__":
    generate_test_data(1000)
    generate_test_excel(10, "performance-tests/data/upload-small.xlsx")
    generate_test_excel(100, "performance-tests/data/upload-medium.xlsx")
    generate_test_excel(1000, "performance-tests/data/upload-large.xlsx")
