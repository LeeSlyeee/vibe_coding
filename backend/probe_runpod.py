
import os
import requests
from dotenv import load_dotenv

load_dotenv()
raw_url = os.getenv('RUNPOD_LLM_URL').replace('/v1', '') # Strip /v1 to get base
api_key = os.getenv('RUNPOD_API_KEY')

print(f"DEBUG: Probing Base URL: {raw_url}")

# List of candidates to try
paths = [
    "/v1/models",
    "/models",
    "/api/tags",   # Ollama
    "/generate",   # TGI?
    "/",           # Root
]

for p in paths:
    # TRY GET
    try:
        url = f"{raw_url}{p}"
        print(f"Trying GET {url}...", end=" ")
        headers = {"Authorization": f"Bearer {api_key}"}
        res = requests.get(url, headers=headers, timeout=5)
        print(f"[{res.status_code}]")
        if res.status_code == 200:
            print(f"SUCCESS! Found endpoint: {url}")
            print(f"Body: {res.text[:100]}")
            break
    except Exception as e:
        print(f"Error: {e}")
