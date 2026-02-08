# Base image with Python 3.10 and CUDA support (Pinning version for stability)
FROM vllm/vllm-openai:v0.6.3.post1

# Working Directory
WORKDIR /app

# Install RunPod SDK and Merging Tools (peft)
RUN pip install runpod huggingface_hub peft accelerate

# [Speed Optimization] Copy handler first to leverage caching
# 1. Copy Handler
COPY src/handler.py /app/handler.py

# 2. [Offline Mode] Copy Pre-downloaded Model Data
# Contains: /app/model_data/base (Llama-3) & /app/model_data/adapter (haruON)
COPY model_data /app/model_data

# 3. Copy Start Script
COPY src/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Overwrite the base image entrypoint
ENTRYPOINT ["/app/start.sh"]
CMD []
