
import os
import sys

# Ensure backend path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.ai_analysis import EmotionAnalysis

if __name__ == "__main__":
    print("Starting Ultra-Fine-Grained (60-Class) AI Training...")
    # Force retrain by deleting old model? No need, logic checks if file exists.
    # Actually logic says "if exists, load".
    # I MUST force retrain.
    # The default behavior of _load_and_train is called ONLY if model missing.
    # But I can call it explicitly.
    
    ai = EmotionAnalysis()
    # Force training call
    print("Forcing _load_and_train...")
    ai._load_and_train()
    print("Training Complete.")
