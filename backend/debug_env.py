
from dotenv import load_dotenv
import os
load_dotenv()
print(f"KEY: '{os.getenv('RUNPOD_API_KEY')}'")
print(f"URL: '{os.getenv('RUNPOD_LLM_URL')}'")
