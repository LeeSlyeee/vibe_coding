#!/bin/bash
echo "🚀 [Start Script] Container Started (Offline vLLM Mode)!"

# Directory Check
if [ -d "/app/model_data/base" ] && [ -d "/app/model_data/adapter" ]; then
    echo "✅ [Start Script] Model files detected."
else
    echo "❌ [Start Script] Critical: Model files missing in /app/model_data"
    ls -R /app
    exit 1
fi

echo "🚀 [Start Script] Starting Handler..."
python3 -u /app/handler.py
