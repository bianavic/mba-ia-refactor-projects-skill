"""Stateless security helpers: password hashing and signed tokens."""
import hashlib
import hmac

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")
_TOKEN_SALT = "auth-token"
_LEGACY_MD5_LENGTH = 32


def hash_password(password):
    return generate_password_hash(password)


def is_modern_hash(value):
    return isinstance(value, str) and value.startswith(_HASH_PREFIXES)


def is_legacy_md5(value):
    return isinstance(value, str) and len(value) == _LEGACY_MD5_LENGTH and not is_modern_hash(value)


def verify_password(stored, password):
    """Check a salted hash; also accepts a legacy unsalted MD5 hash so it can be upgraded on login."""
    if is_modern_hash(stored):
        return check_password_hash(stored, password)
    if is_legacy_md5(stored):
        legacy = hashlib.md5(password.encode()).hexdigest()
        return hmac.compare_digest(stored, legacy)
    return False


def fingerprint(*parts):
    """Short, non-reversible digest of account state bound into a token."""
    return hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()[:32]


def fingerprints_match(expected, received):
    return isinstance(received, str) and hmac.compare_digest(expected, received)


def create_token(secret, data):
    return URLSafeTimedSerializer(secret, salt=_TOKEN_SALT).dumps(data)


def read_token(secret, token, max_age_seconds):
    """Return the token payload, or None when invalid or expired."""
    try:
        return URLSafeTimedSerializer(secret, salt=_TOKEN_SALT).loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
