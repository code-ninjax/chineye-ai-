"""
auth.py - Authentication utilities (JWT, password hashing)
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
# Lazy import for JWT to avoid startup crashes if dependency missing
JWTError = None
jwt = None

def _ensure_jose():
    global JWTError, jwt
    if jwt is None or JWTError is None:
        try:
            from jose import JWTError as _JWTError, jwt as _jwt
            JWTError = _JWTError
            jwt = _jwt
        except Exception as e:
            raise ImportError("JWT library not available. Ensure 'python-jose[cryptography]' is installed.")

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 (Python standard library)
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password with salt
    """
    # Generate a random salt
    salt = secrets.token_hex(32)
    
    # Hash password with salt using PBKDF2
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    
    # Return salt + hash combined
    return f"{salt}${pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        salt, pwd_hash = hashed_password.split('$')
        
        # Hash the plain password with the stored salt
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        # Compare hashes
        return new_hash.hex() == pwd_hash
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire_dt = datetime.utcnow() + expires_delta
    else:
        expire_dt = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Use numeric timestamp for maximum compatibility in serverless runtimes
    exp_ts = int(expire_dt.timestamp())
    to_encode.update({"exp": exp_ts})
    # Import jose lazily to prevent import-time crashes in serverless runtimes
    _ensure_jose()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        _ensure_jose()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        # Includes missing library or invalid token
        return None


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from JWT token
    
    Args:
        token: JWT token
        
    Returns:
        user_id if valid, None otherwise
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None
