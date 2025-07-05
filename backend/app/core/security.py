"""
Security utilities for authentication and authorization
"""
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Union
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (supports bcrypt and legacy SHA-256)"""
    try:
        # Try bcrypt first (current standard)
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback: check if it's a legacy SHA-256 hash
        try:
            import hashlib
            legacy_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if legacy_hash == hashed_password:
                logger.warning(f"User authenticated with legacy SHA-256 hash - should be migrated to bcrypt")
                return True
        except Exception as e:
            logger.error(f"Password verification error: {e}")
        return False


def migrate_legacy_password_hash(user_id: str, new_password: str) -> None:
    """Migrate a user's password from legacy SHA-256 to bcrypt"""
    from .database_service import get_db_session
    from sqlalchemy import text
    
    try:
        with get_db_session() as session:
            new_hash = hash_password(new_password)
            session.execute(text(
                "UPDATE users SET hashed_password = :new_hash WHERE id = :user_id"
            ), {"new_hash": new_hash, "user_id": user_id})
            
        logger.info(f"Successfully migrated password hash for user {user_id} to bcrypt")
    except Exception as e:
        logger.error(f"Failed to migrate password hash for user {user_id}: {e}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def extract_token_from_header(authorization: str) -> Optional[str]:
    """Extract token from Authorization header"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    return authorization.replace("Bearer ", "")