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
                    return text  # 이미 암호화된 데이터는 재암호화하지 않음
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
# [Security] ENCRYPTION_KEY 누락 시 서버 기동 자체를 차단 (Fail Fast)
# crypto_manager = None 으로 조용히 넘어가는 것은 암호화 없이 민감 데이터를 저장하는 보안 사고로 이어짐
try:
    crypto_manager = EncryptionManager()
except ValueError as e:
    import sys
    print(f"[CRITICAL] 암호화 초기화 실패: {e}  — ENCRYPTION_KEY 를 .env 에 설정하세요.")
    sys.exit(1)
except Exception as e:
    import sys
    print(f"[CRITICAL] 암호화 초기화 중 알 수 없는 오류: {e}")
    sys.exit(1)
