"""
Authentication service for PostgreSQL
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .database_service import get_db_session
from .security import verify_password, hash_password, create_access_token, verify_token
from ..models.user import User

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for PostgreSQL"""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using PostgreSQL"""
        with get_db_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": str(user.id),  # Convert UUID to string
                    "email": user.email,
                    "name": user.name,
                    "hashed_password": user.hashed_password,
                    "timezone": user.timezone,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using PostgreSQL"""
        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "hashed_password": user.hashed_password,
                    "timezone": user.timezone,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
            return None
    
    @staticmethod
    def create_user(email: str, name: str, password: str, is_admin: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        with get_db_session() as session:
            # Check if user already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                return None
            
            # Create new user
            import uuid
            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name,
                hashed_password=hash_password(password),
                is_active=True,
                is_admin=is_admin
            )
            session.add(new_user)
            session.commit()
            
            return {
                "id": str(new_user.id),
                "email": new_user.email,
                "name": new_user.name,
                "is_active": new_user.is_active,
                "is_admin": new_user.is_admin,
                "created_at": new_user.created_at
            }
    
    @staticmethod
    def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data + token"""
        logger.info(f"🔐 Attempting login for: {email}")
        
        user = AuthService.get_user_by_email(email)
        if not user:
            logger.warning(f"❌ User not found: {email}")
            return None
        
        if not user.get("is_active", False):
            logger.warning(f"❌ User inactive: {email}")
            return None
        
        if not verify_password(password, user["hashed_password"]):
            logger.warning(f"❌ Invalid password for: {email}")
            return None
        
        # Create token
        token = create_access_token({"sub": user["id"], "email": user["email"]})
        
        logger.info(f"✅ Login successful for: {email}")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "is_admin": user["is_admin"]
            }
        }
    
    @staticmethod
    def register_user(email: str, name: str, password: str) -> Optional[Dict[str, Any]]:
        """Register a new user and return login data"""
        user = AuthService.create_user(email, name, password, is_admin=False)
        if not user:
            return None
        
        # Automatically log in the new user
        return AuthService.login_user(email, password)
    
    @staticmethod
    def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify token and return user data"""
        try:
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            return AuthService.get_user_by_id(user_id)
        
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None