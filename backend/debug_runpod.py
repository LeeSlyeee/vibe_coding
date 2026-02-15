
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('RUNPOD_API_KEY')
base_url = os.getenv('RUNPOD_LLM_URL').rstrip('/')

print(f"DEBUG: Base URL from Env: {base_url}")

# Test 1: List Models
try:
    url = f"{base_url}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    print(f"Test 1: GET {url}")
    res = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text[:200]}")
except Exception as e:
    print(f"Test 1 Error: {e}")

# Test 2: Chat Completion
try:
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    print(f"\nTest 2: POST {url}")
    res = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text[:200]}")
except Exception as e:
    print(f"Test 2 Error: {e}")
