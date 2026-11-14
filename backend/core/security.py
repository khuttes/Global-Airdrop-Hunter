import secrets
import hashlib
import hmac
from typing import Optional
from datetime import datetime, timedelta


def generate_token(length: int = 32) -> str:
    return secrets.token_hex(length)


def generate_api_token() -> str:
    return generate_token(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(provided: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_token(provided), stored_hash)


def create_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TokenManager:
    def __init__(self):
        self._token: Optional[str] = None
        self._token_hash: Optional[str] = None
        self._created_at: Optional[datetime] = None

    def generate(self) -> str:
        self._token = generate_api_token()
        self._token_hash = create_token_hash(self._token)
        self._created_at = datetime.utcnow()
        return self._token

    def get_token(self) -> Optional[str]:
        return self._token

    def get_token_hash(self) -> Optional[str]:
        return self._token_hash

    def validate(self, token: str) -> bool:
        if not self._token_hash or not token:
            return False
        return verify_token(token, self._token_hash)

    def is_expired(self, max_age_hours: int = 24) -> bool:
        if not self._created_at:
            return True
        return datetime.utcnow() - self._created_at > timedelta(hours=max_age_hours)

    def clear(self):
        self._token = None
        self._token_hash = None
        self._created_at = None


token_manager = TokenManager()