"""
Authentication API endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import List

from ..core.auth_service import AuthService
from ..schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# Removed create_token wrapper - using create_access_token directly


def get_current_user_dependency(authorization: str = Header(None)):
    """FastAPI dependency for getting current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        user = AuthService.verify_user_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token or user not found")
            
        return {
            'id': user['id'],
            'sub': user['id'],  # Add 'sub' for compatibility
            'email': user['email'], 
            'name': user['name'],
            'timezone': user['timezone'],
            'is_active': user['is_active'],
            'is_admin': user['is_admin'],
            'created_at': user['created_at']
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
        
        user = AuthService.verify_user_token(token)
        if not user:
            return None
            
        return {
            'id': user['id'],
            'sub': user['id'],  # Add 'sub' for compatibility
            'email': user['email'], 
            'name': user['name'],
            'timezone': user['timezone'],
            'is_active': user['is_active'],
            'is_admin': user['is_admin'],
            'created_at': user['created_at']
        }
    except Exception as e:
        logger.error(f"Authentication helper error: {e}")
        return None


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    logger.info(f"🔐 REGISTRATION ATTEMPT - Email: {user_data.email}")
    
    result = AuthService.register_user(user_data.email, user_data.name, user_data.password)
    
    if not result:
        logger.warning(f"❌ REGISTRATION FAILED - Email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    logger.info(f"✅ REGISTRATION SUCCESS - User created: {user_data.email}")
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["access_token"],  # Using same token for now
        expires_in=86400
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Authenticate user and return tokens"""
    logger.info(f"🔐 LOGIN ATTEMPT - Email: {user_data.email}")
    
    result = AuthService.login_user(user_data.email, user_data.password)
    
    if not result:
        logger.warning(f"❌ LOGIN FAILED - Invalid credentials: {user_data.email}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    logger.info(f"✅ LOGIN SUCCESS - User: {user_data.email}, Token created")
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["access_token"],  # Using same token for now
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
            id=current_user['id'],  # Use 'id' instead of 'sub'
            email=current_user['email'],
            name=current_user['name'],
            timezone=current_user['timezone'],
            is_active=current_user['is_active'],
            is_admin=current_user['is_admin'],
            created_at=current_user['created_at'].isoformat()  # Convert datetime to string
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