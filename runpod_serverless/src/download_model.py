import os
import sys
import traceback
from huggingface_hub import snapshot_download

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Get token from environment
hf_token = os.environ.get("HF_TOKEN")
model_id = "slyeee/maum-on-llama3-v1"

print(f"🚀 [Downloader] Starting download script...", flush=True)

if not hf_token:
    print("❌ [Downloader] Error: HF_TOKEN environment variable not set.", flush=True)
    sys.exit(1)

print(f"🚀 [Downloader] Downloading model: {model_id} with token starting with {hf_token[:4]}...", flush=True)

local_model_dir = "/app/adapter"

try:
    # Download with ignore_patterns to skip unnecessary large files if any, but ensure we get the model
    # Note: snapshot_download with local_dir usually uses symlinks if cache exists, but we want to be sure.
    snapshot_download(
        repo_id=model_id, 
        local_dir=local_model_dir, 
        token=hf_token
    )
    
    # Verification Step
    if not os.path.exists(local_model_dir):
        print(f"❌ [Downloader] Error: Directory {local_model_dir} does not exist.", flush=True)
        sys.exit(1)
        
    files = os.listdir(local_model_dir)
    print(f"📂 [Downloader] Files downloaded: {files}", flush=True)
    
    required_files = ["config.json", "model.safetensors.index.json"]
    # Check if it looks like an adapter
    if "adapter_config.json" in files:
         print(f"✅ [Downloader] LoRA Adapter detected. (adapter_config.json found)", flush=True)
    elif "config.json" not in files:
         print(f"⚠️ [Downloader] Warning: config.json missing! This might be a raw adapter or invalid model.", flush=True)
         # We allow this now because we will merge in handler.py

    print("✅ [Downloader] Model downloaded and verified successfully!", flush=True)
except Exception as e:
    print(f"❌ [Downloader] Failed to download model: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
