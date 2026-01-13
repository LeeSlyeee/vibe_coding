import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_analysis import ai_analyzer

print("Starting checks...")
if hasattr(ai_analyzer, 'train_comment_model'):
    print("Method exists. calling...")
    ai_analyzer.train_comment_model()
    print("Training finished call.")
else:
    print("Method train_comment_model not found.")
