import os
from cryptography.fernet import Fernet
from config import Config

class EncryptionManager:
    def __init__(self, key=None):
        if key:
            self.fernet = Fernet(key)
        else:
            # Load from Config or Env
            env_key = os.environ.get('ENCRYPTION_KEY') or Config.ENCRYPTION_KEY
            if not env_key:
                raise ValueError("ENCRYPTION_KEY is missing!")
            self.fernet = Fernet(env_key)

    def encrypt(self, text):
        if not text:
            return ""
        if isinstance(text, str):
            try:
                # If already encrypted (starts with gAAAA), return as is (Idempotency)
                if text.startswith('gAAAA') and len(text) > 20: 
                    # Try decrypting to verify? No, too expensive.
                    # Just assume if it looks like Fernet token, it is.
                    # But user input might start with gAAAA. 
                    # Better to just encrypt everything. But migration needs care.
                    pass
                return self.fernet.encrypt(text.encode()).decode()
            except Exception as e:
                print(f"Encryption error: {e}")
                return text
        return text

    def decrypt(self, token):
        if not token:
            return ""
        if not isinstance(token, str):
            return token
        try:
            return self.fernet.decrypt(token.encode()).decode()
        except Exception:
            # If decryption fails, it might be plain text (during transition)
            return token

# Global Instance
# Initialize lazily or on import provided env is loaded
try:
    crypto_manager = EncryptionManager()
except:
    crypto_manager = None 
