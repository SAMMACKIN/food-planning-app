"""
Authentication service using the unified database abstraction layer
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database_service import get_db_session, db_service
from .security import verify_password, hash_password, create_access_token, verify_token
from ..models.simple_models import User

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service supporting both SQLite and PostgreSQL"""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email - works with both SQLite and PostgreSQL"""
        with get_db_session() as session:
            if db_service.use_sqlite:
                # SQLite query
                session.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = session.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "email": row[1], 
                        "name": row[2],
                        "hashed_password": row[3],
                        "timezone": row[4],
                        "is_active": bool(row[5]),
                        "is_admin": bool(row[6]),
                        "created_at": row[7]
                    }
                return None
            else:
                # SQLAlchemy query
                user = session.query(User).filter(User.email == email).first()
                if user:
                    return {
                        "id": user.id,
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
        """Get user by ID - works with both SQLite and PostgreSQL"""
        with get_db_session() as session:
            if db_service.use_sqlite:
                # SQLite query
                session.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = session.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "email": row[1],
                        "name": row[2], 
                        "hashed_password": row[3],
                        "timezone": row[4],
                        "is_active": bool(row[5]),
                        "is_admin": bool(row[6]),
                        "created_at": row[7]
                    }
                return None
            else:
                # SQLAlchemy query
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    return {
                        "id": user.id,
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
    def create_user(email: str, name: str, password: str, is_admin: bool = False) -> Dict[str, Any]:
        """Create a new user - works with both SQLite and PostgreSQL"""
        import uuid
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        with get_db_session() as session:
            if db_service.use_sqlite:
                # SQLite insert
                session.execute('''
                    INSERT INTO users (id, email, name, hashed_password, is_admin, is_active, timezone)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, email, name, hashed_password, is_admin, True, "UTC"))
            else:
                # SQLAlchemy insert
                user = User(
                    id=user_id,
                    email=email,
                    name=name,
                    hashed_password=hashed_password,
                    is_admin=is_admin,
                    is_active=True,
                    timezone="UTC"
                )
                session.add(user)
        
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "is_admin": is_admin,
            "is_active": True,
            "timezone": "UTC"
        }
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = AuthService.get_user_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: User not found for email: {email}")
            return None
        
        if not user["is_active"]:
            logger.warning(f"Authentication failed: Inactive user: {email}")
            return None
        
        if not verify_password(password, user["hashed_password"]):
            logger.warning(f"Authentication failed: Invalid password for email: {email}")
            return None
        
        logger.info(f"Authentication successful for user: {email}")
        return user
    
    @staticmethod
    def login_user(email: str, password: str) -> Optional[Dict[str, str]]:
        """Login user and return access token"""
        user = AuthService.authenticate_user(email, password)
        if not user:
            return None
        
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        }
    
    @staticmethod
    def register_user(email: str, name: str, password: str) -> Optional[Dict[str, str]]:
        """Register a new user and return access token"""
        # Check if user already exists
        existing_user = AuthService.get_user_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed: User already exists: {email}")
            return None
        
        # Create new user
        user = AuthService.create_user(email, name, password)
        
        # Generate access token
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        }
        
        access_token = create_access_token(token_data)
        
        logger.info(f"User registered successfully: {email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        }
    
    @staticmethod
    def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify user token and return user data"""
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = AuthService.get_user_by_id(user_id)
        if not user or not user["is_active"]:
            return None
        
        return user