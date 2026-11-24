import base64
import os
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .config import settings

def _get_fernet_key() -> bytes:
    # Derive a stable 32-byte url-safe base64 key from settings.SECRET_KEY
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"antigravity_yt_shorts_salt_2026",
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))

_fernet = Fernet(_get_fernet_key())

def encrypt_token(plain_token: str) -> str:
    """Encrypts raw OAuth tokens before database persistence."""
    if not plain_token:
        return ""
    return _fernet.encrypt(plain_token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts stored OAuth tokens for API usage."""
    if not encrypted_token:
        return ""
    try:
        return _fernet.decrypt(encrypted_token.encode()).decode()
    except Exception:
        return ""

def generate_state_token() -> str:
    """Generates a cryptographically secure OAuth state parameter."""
    return secrets.token_urlsafe(32)

def validate_safe_path(target_path: Path, allowed_root: Path) -> bool:
    """Verifies that target_path resides safely within allowed_root, preventing path traversal."""
    try:
        resolved_target = target_path.resolve()
        resolved_root = allowed_root.resolve()
        return str(resolved_target).startswith(str(resolved_root))
    except Exception:
        return False
