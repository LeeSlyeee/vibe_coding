
import os
import requests
from dotenv import load_dotenv

load_dotenv()
pod_id = "mp2w6kb0npg0tp" # Extracted from user env
api_key = os.getenv('RUNPOD_API_KEY')

print(f"DEBUG: Probing Pod ID: {pod_id}")

# Try 8000, 80, 5000
ports = ["8000", "80", "5000", "3000"]
paths = ["/v1/models", "/models", "/", "/docs"]

for port in ports:
    base_url = f"https://{pod_id}-{port}.proxy.runpod.net"
    print(f"\n--- Checking Port {port} ---")
    for p in paths:
        try:
            url = f"{base_url}{p}"
            # print(f"GET {url}...", end=" ")
            headers = {"Authorization": f"Bearer {api_key}"}
            res = requests.get(url, headers=headers, timeout=3)
            print(f"GET {url} -> [{res.status_code}]")
            if res.status_code == 200:
                print(f"!!! SUCCESS !!! Found Service at: {url}")
                print(f"Body snippet: {res.text[:100]}")
        except Exception as e:
            # print(f"Err: {e}")
            pass
