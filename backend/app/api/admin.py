"""
Admin-only API endpoints for user management and platform statistics
"""
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import text

from ..core.database_service import get_db_session
from ..core.auth_service import AuthService
from ..core.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class PasswordResetRequest(BaseModel):
    new_password: str


def get_current_user(authorization: str = None):
    """Get current user using AuthService"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        user_data = AuthService.verify_user_token(token)
        
        if not user_data:
            return None
        
        return {
            'id': user_data['id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'timezone': user_data['timezone'],
            'is_active': user_data['is_active'],
            'is_admin': user_data['is_admin'],
            'created_at': user_data['created_at'].isoformat() if user_data['created_at'] else None
        }
    
    except Exception:
        return None


def require_admin(authorization: str = Header(None)):
    """Decorator helper to require admin access"""
    current_user = get_current_user(authorization)
    if not current_user or not current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users")
async def get_all_users(authorization: str = Header(None)):
    """Admin endpoint to view all users"""
    require_admin(authorization)
    
    with get_db_session() as session:
        result = session.execute(text('''
            SELECT id, email, name, timezone, is_active, is_admin, created_at, hashed_password
            FROM users 
            ORDER BY created_at DESC
        '''))
        users = result.fetchall()
        
        return [
            {
                'id': str(user[0]),
                'email': user[1],
                'name': user[2],
                'timezone': user[3],
                'is_active': bool(user[4]),
                'is_admin': bool(user[5]),
                'created_at': user[6].isoformat() if user[6] else None,
                'hashed_password': user[7]
            }
            for user in users
        ]


@router.get("/family/all")
async def get_all_family_members(authorization: str = Header(None)):
    """Admin endpoint to view all family members across all users"""
    require_admin(authorization)
    
    try:
        with get_db_session() as session:
            result = session.execute(text('''
                SELECT fm.id, fm.user_id, fm.name, fm.age, fm.dietary_restrictions, fm.preferences, fm.created_at,
                       u.email as user_email, u.name as user_name
                FROM family_members fm
                JOIN users u ON fm.user_id = u.id
                ORDER BY u.email, fm.name
            '''))
            family_members = result.fetchall()
            
            response_data = []
            for member in family_members:
                try:
                    # Parse dietary_restrictions with better error handling
                    dietary_restrictions = []
                    if member[4]:  # dietary_restrictions field
                        try:
                            if isinstance(member[4], str):
                                dietary_restrictions = json.loads(member[4])
                            elif isinstance(member[4], list):
                                dietary_restrictions = member[4]
                            else:
                                dietary_restrictions = []
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Failed to parse dietary_restrictions for family member {member[0]}: {e}")
                            dietary_restrictions = []
                    
                    # Parse preferences with better error handling
                    preferences = {}
                    if member[5]:  # preferences field
                        try:
                            if isinstance(member[5], str):
                                preferences = json.loads(member[5])
                            elif isinstance(member[5], dict):
                                preferences = member[5]
                            else:
                                preferences = {}
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Failed to parse preferences for family member {member[0]}: {e}")
                            preferences = {}
                    
                    response_data.append({
                        'id': str(member[0]),
                        'user_id': str(member[1]),
                        'name': member[2],
                        'age': member[3],
                        'dietary_restrictions': dietary_restrictions,
                        'preferences': preferences,
                        'created_at': member[6].isoformat() if member[6] else None,
                        'user_email': member[7],
                        'user_name': member[8]
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing family member {member[0] if len(member) > 0 else 'unknown'}: {e}")
                    # Continue processing other members
                    continue
            
            return response_data
            
    except Exception as e:
        logger.error(f"Critical error in admin family endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving family members: {str(e)}")


@router.get("/stats")
async def get_admin_stats(authorization: str = Header(None)):
    """Admin endpoint to get platform statistics"""
    require_admin(authorization)
    
    try:
        with get_db_session() as session:
            stats = {}
            
            # Get total users (excluding admins)
            try:
                result = session.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = false"))
                stats['total_users'] = result.fetchone()[0]
            except Exception as e:
                logger.error(f"Error getting total users: {e}")
                stats['total_users'] = 0
            
            # Get total family members
            try:
                result = session.execute(text("SELECT COUNT(*) FROM family_members"))
                stats['total_family_members'] = result.fetchone()[0]
            except Exception as e:
                logger.error(f"Error getting family members count: {e}")
                stats['total_family_members'] = 0
            
            # Get total pantry items
            try:
                result = session.execute(text("SELECT COUNT(*) FROM pantry_items"))
                stats['total_pantry_items'] = result.fetchone()[0]
            except Exception as e:
                logger.error(f"Error getting pantry items count: {e}")
                stats['total_pantry_items'] = 0
            
            # Get recent registrations (last 30 days)
            try:
                result = session.execute(text("""
                    SELECT COUNT(*) FROM users 
                    WHERE is_admin = false AND created_at >= NOW() - INTERVAL '30 days'
                """))
                stats['recent_registrations'] = result.fetchone()[0]
            except Exception as e:
                logger.error(f"Error getting recent registrations: {e}")
                stats['recent_registrations'] = 0
            
            # Get total meal plans (table might not exist)
            try:
                result = session.execute(text("SELECT COUNT(*) FROM meal_plans"))
                stats['total_meal_plans'] = result.fetchone()[0]
            except Exception as e:
                logger.warning(f"meal_plans table not accessible: {e}")
                stats['total_meal_plans'] = 0
            
            # Get total recipes
            try:
                result = session.execute(text("SELECT COUNT(*) FROM recipes_v2"))
                stats['total_recipes'] = result.fetchone()[0]
            except Exception as e:
                logger.warning(f"recipes_v2 table not accessible: {e}")
                stats['total_recipes'] = 0
            
            return stats
            
    except Exception as e:
        logger.error(f"Critical error in admin stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving admin statistics: {str(e)}")


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: str, authorization: str = Header(None)):
    """Admin endpoint to delete any user account"""
    current_user = require_admin(authorization)
    
    # Prevent admin from deleting themselves
    if current_user['id'] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    try:
        with get_db_session() as session:
            # Check if user exists
            result = session.execute(text("SELECT id, email, is_admin FROM users WHERE id = :user_id"), {"user_id": user_id})
            target_user = result.fetchone()
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Prevent deleting other admin accounts for safety
            if target_user[2]:  # is_admin
                raise HTTPException(status_code=400, detail="Cannot delete other admin accounts")
            
            # Delete user data in order (foreign key constraints)
            try:
                session.execute(text("DELETE FROM meal_reviews WHERE user_id = :user_id"), {"user_id": user_id})
            except Exception:
                # Table doesn't exist, skip
                pass
            
            try:
                session.execute(text("DELETE FROM meal_plans WHERE user_id = :user_id"), {"user_id": user_id})
            except Exception:
                # Table doesn't exist, skip
                pass
            
            session.execute(text("DELETE FROM pantry_items WHERE user_id = :user_id"), {"user_id": user_id})
            session.execute(text("DELETE FROM family_members WHERE user_id = :user_id"), {"user_id": user_id})
            session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            
            return {
                "message": "User account deleted successfully", 
                "deleted_user_email": target_user[1]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user account: {str(e)}")


@router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str, 
    request: PasswordResetRequest, 
    authorization: str = Header(None)
):
    """Admin endpoint to reset a user's password"""
    require_admin(authorization)
    
    try:
        with get_db_session() as session:
            # Check if user exists
            result = session.execute(text("SELECT id, email FROM users WHERE id = :user_id"), {"user_id": user_id})
            target_user = result.fetchone()
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Hash the new password
            hashed_password = hash_password(request.new_password)
            
            # Update user's password
            session.execute(text("UPDATE users SET hashed_password = :hashed_password WHERE id = :user_id"), 
                          {"hashed_password": hashed_password, "user_id": user_id})
            
            return {
                "message": "Password reset successfully for user", 
                "user_email": target_user[1]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")


@router.get("/pantry/all")
async def get_all_pantry_items(authorization: str = Header(None)):
    """Admin endpoint to view all pantry items across all users"""
    require_admin(authorization)
    
    try:
        with get_db_session() as session:
            result = session.execute(text('''
                SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
                       i.name as ingredient_name, 
                       CASE WHEN ic.name IS NOT NULL THEN ic.name ELSE 'Other' END as ingredient_category, 
                       i.unit,
                       u.email as user_email, u.name as user_name
                FROM pantry_items p
                JOIN ingredients i ON p.ingredient_id = i.id
                LEFT JOIN ingredient_categories ic ON i.category_id = ic.id
                JOIN users u ON p.user_id = u.id
                ORDER BY u.email, ic.name, i.name
            '''))
            pantry_items = result.fetchall()
            
            return [
                {
                    'user_id': str(item[0]),
                    'ingredient_id': str(item[1]),
                    'quantity': item[2],
                    'expiration_date': item[3].strftime('%Y-%m-%d') if item[3] else None,
                    'updated_at': item[4].isoformat() if item[4] else None,
                    'ingredient_name': item[5],
                    'ingredient_category': item[6],
                    'ingredient_unit': item[7],
                    'user_email': item[8],
                    'user_name': item[9]
                }
                for item in pantry_items
            ]
            
    except Exception as e:
        logger.error(f"Critical error in admin pantry endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pantry items: {str(e)}")