import os
import sys
from huggingface_hub import snapshot_download

HF_TOKEN = os.getenv("HF_TOKEN")
BASE_MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
ADAPTER_ID = "slyeee/maum-on-llama3-v1"
MODEL_DIR = "./model_data"

print(f"🚀 [Local Build] Starting Download...")

try:
    print(f"⬇️ Downloading Base Model: {BASE_MODEL_ID}...")
    snapshot_download(
        repo_id=BASE_MODEL_ID, 
        local_dir=f"{MODEL_DIR}/base", 
        token=HF_TOKEN,
        ignore_patterns=["*.pth", "*.pt", "original/*"] # PyTorch weight 제외 (Safetensors만)
    )

    print(f"⬇️ Downloading Adapter: {ADAPTER_ID}...")
    snapshot_download(
        repo_id=ADAPTER_ID, 
        local_dir=f"{MODEL_DIR}/adapter", 
        token=HF_TOKEN
    )
    
    print("✅ All models downloaded successfully to ./model_data")
except Exception as e:
    print(f"❌ Error during download: {e}")
    sys.exit(1)
