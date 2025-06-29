"""
Authentication API endpoints
"""
import uuid
import sqlite3
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import List

from ..core.database import get_db_path
from ..core.security import hash_password, verify_password, create_access_token, verify_token
from ..schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def create_token(user_id: str) -> str:
    """Create JWT token - wrapper for new security module"""
    return create_access_token({"sub": user_id})


def get_current_user_dependency(authorization: str = Header(None)):
    """FastAPI dependency for getting current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, timezone, is_active, is_admin, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            'id': user[0],
            'email': user[1], 
            'name': user[2],
            'timezone': user[3],
            'is_active': bool(user[4]),
            'is_admin': bool(user[5]),
            'created_at': user[6]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def get_current_user(authorization: str = None):
    """Helper function for legacy endpoints"""
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, timezone, is_active, is_admin, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
            
        return {
            'id': user[0],
            'email': user[1], 
            'name': user[2],
            'timezone': user[3],
            'is_active': bool(user[4]),
            'is_admin': bool(user[5]),
            'created_at': user[6]
        }
    except Exception as e:
        logger.error(f"Authentication helper error: {e}")
        return None


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    cursor.execute(
        "INSERT INTO users (id, email, hashed_password, name) VALUES (?, ?, ?, ?)",
        (user_id, user_data.email, hashed_password, user_data.name)
    )
    conn.commit()
    conn.close()
    
    # Create tokens
    access_token = create_token(user_id)
    refresh_token = create_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Authenticate user and return tokens"""
    logger.info(f"🔐 LOGIN ATTEMPT - Email: {user_data.email}")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, hashed_password, is_active, is_admin FROM users WHERE email = ?", (user_data.email,))
    user = cursor.fetchone()
    
    if not user:
        logger.warning(f"❌ LOGIN FAILED - User not found: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    logger.info(f"📋 User found - ID: {user[0]}, Active: {user[2]}, Admin: {user[3]}")
    
    password_valid = verify_password(user_data.password, user[1])
    logger.info(f"🔑 Password verification: {password_valid}")
    
    if not password_valid:
        logger.warning(f"❌ LOGIN FAILED - Invalid password for: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user[2]:  # Check is_active
        logger.warning(f"❌ LOGIN FAILED - Inactive user: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    conn.close()
    
    # Create tokens
    access_token = create_token(user[0])
    refresh_token = create_token(user[0])
    
    logger.info(f"✅ LOGIN SUCCESS - User: {user_data.email}, Token created")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(authorization: str = Header(None)):
    """Get current authenticated user information"""
    logger.info("🔍 /auth/me called")
    logger.info(f"📋 Authorization header present: {bool(authorization)}")
    
    if authorization:
        logger.info(f"🔐 Auth header value (first 20 chars): {authorization[:20]}...")
    
    # If no authorization header, return 401
    if not authorization:
        logger.warning("❌ No authorization header provided")
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        current_user = get_current_user_dependency(authorization)
        logger.info(f"✅ Authentication successful for user: {current_user['email']}")
        logger.info(f"👤 User details - Admin: {current_user['is_admin']}, Active: {current_user['is_active']}")
        
        return UserResponse(
            id=current_user['sub'],
            email=current_user['email'],
            name=current_user['name'],
            timezone=current_user['timezone'],
            is_active=current_user['is_active'],
            is_admin=current_user['is_admin'],
            created_at=current_user['created_at']
        )
    except HTTPException as e:
        logger.error(f"❌ Authentication failed with HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"❌ Authentication failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.delete("/delete-account")
async def delete_user_account(authorization: str = Header(None)):
    """Delete current user account and all associated data"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    
    # Prevent admin account deletion for safety
    if current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Cannot delete admin account. Use admin panel to manage accounts.")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Delete user data in order (foreign key constraints)
        cursor.execute("DELETE FROM meal_reviews WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM pantry_items WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")