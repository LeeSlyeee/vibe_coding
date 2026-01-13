import sys
print(f"Python: {sys.version}")
try:
    import tensorflow as tf
    print(f"TensorFlow: {tf.__version__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
