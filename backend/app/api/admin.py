"""
Admin-only API endpoints for user management and platform statistics
"""
import sqlite3
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from ..core.database import get_db_connection
from ..core.security import verify_token, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


class PasswordResetRequest(BaseModel):
    new_password: str


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    user_data = verify_token(token)
    
    if not user_data:
        return None
    
    # Get full user details from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, email, name, timezone, is_active, is_admin, created_at 
            FROM users WHERE id = ?
        """, (user_data,))
        user = cursor.fetchone()
        
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
    finally:
        conn.close()


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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, name, timezone, is_active, is_admin, created_at, hashed_password
            FROM users 
            ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        
        return [
            {
                'id': user[0],
                'email': user[1],
                'name': user[2],
                'timezone': user[3],
                'is_active': bool(user[4]),
                'is_admin': bool(user[5]),
                'created_at': user[6],
                'hashed_password': user[7]
            }
            for user in users
        ]
        
    finally:
        conn.close()


@router.get("/family/all")
async def get_all_family_members(authorization: str = Header(None)):
    """Admin endpoint to view all family members across all users"""
    require_admin(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT fm.id, fm.user_id, fm.name, fm.age, fm.dietary_restrictions, fm.preferences, fm.created_at,
                   u.email as user_email, u.name as user_name
            FROM family_members fm
            JOIN users u ON fm.user_id = u.id
            ORDER BY u.email, fm.name
        ''')
        family_members = cursor.fetchall()
        
        result = []
        for member in family_members:
            # Parse dietary_restrictions and preferences from JSON/eval
            try:
                dietary_restrictions = json.loads(member[4]) if member[4] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    dietary_restrictions = eval(member[4]) if member[4] else []
                except:
                    dietary_restrictions = []
            
            try:
                preferences = json.loads(member[5]) if member[5] else {}
            except (json.JSONDecodeError, TypeError):
                try:
                    preferences = eval(member[5]) if member[5] else {}
                except:
                    preferences = {}
            
            result.append({
                'id': member[0],
                'user_id': member[1],
                'name': member[2],
                'age': member[3],
                'dietary_restrictions': dietary_restrictions,
                'preferences': preferences,
                'created_at': member[6],
                'user_email': member[7],
                'user_name': member[8]
            })
        
        return result
        
    finally:
        conn.close()


@router.get("/stats")
async def get_admin_stats(authorization: str = Header(None)):
    """Admin endpoint to get platform statistics"""
    require_admin(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get total users (excluding admins)
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
        total_users = cursor.fetchone()[0]
        
        # Get total family members
        cursor.execute("SELECT COUNT(*) FROM family_members")
        total_family_members = cursor.fetchone()[0]
        
        # Get total pantry items
        cursor.execute("SELECT COUNT(*) FROM pantry_items")
        total_pantry_items = cursor.fetchone()[0]
        
        # Get recent registrations (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE is_admin = 0 AND created_at >= datetime('now', '-30 days')
        """)
        recent_registrations = cursor.fetchone()[0]
        
        # Get total meal plans (if table exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM meal_plans")
            total_meal_plans = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            total_meal_plans = 0
        
        return {
            'total_users': total_users,
            'total_family_members': total_family_members,
            'total_pantry_items': total_pantry_items,
            'total_meal_plans': total_meal_plans,
            'recent_registrations': recent_registrations
        }
        
    finally:
        conn.close()


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: str, authorization: str = Header(None)):
    """Admin endpoint to delete any user account"""
    current_user = require_admin(authorization)
    
    # Prevent admin from deleting themselves
    if current_user['id'] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id, email, is_admin FROM users WHERE id = ?", (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent deleting other admin accounts for safety
        if target_user[2]:  # is_admin
            raise HTTPException(status_code=400, detail="Cannot delete other admin accounts")
        
        # Delete user data in order (foreign key constraints)
        # Check if meal_reviews table exists
        try:
            cursor.execute("DELETE FROM meal_reviews WHERE user_id = ?", (user_id,))
        except sqlite3.OperationalError:
            # Table doesn't exist, skip
            pass
        
        # Check if meal_plans table exists
        try:
            cursor.execute("DELETE FROM meal_plans WHERE user_id = ?", (user_id,))
        except sqlite3.OperationalError:
            # Table doesn't exist, skip
            pass
        
        cursor.execute("DELETE FROM pantry_items WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        
        return {
            "message": "User account deleted successfully", 
            "deleted_user_email": target_user[1]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user account: {str(e)}")
    finally:
        conn.close()


@router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str, 
    request: PasswordResetRequest, 
    authorization: str = Header(None)
):
    """Admin endpoint to reset a user's password"""
    require_admin(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash the new password
        hashed_password = hash_password(request.new_password)
        
        # Update user's password
        cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        
        return {
            "message": "Password reset successfully for user", 
            "user_email": target_user[1]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")
    finally:
        conn.close()


@router.get("/pantry/all")
async def get_all_pantry_items(authorization: str = Header(None)):
    """Admin endpoint to view all pantry items across all users"""
    require_admin(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
                   i.name as ingredient_name, i.category, i.unit,
                   u.email as user_email, u.name as user_name
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            JOIN users u ON p.user_id = u.id
            ORDER BY u.email, i.category, i.name
        ''')
        pantry_items = cursor.fetchall()
        
        return [
            {
                'user_id': item[0],
                'ingredient_id': item[1],
                'quantity': item[2],
                'expiration_date': item[3],
                'updated_at': item[4],
                'ingredient_name': item[5],
                'ingredient_category': item[6],
                'ingredient_unit': item[7],
                'user_email': item[8],
                'user_name': item[9]
            }
            for item in pantry_items
        ]
        
    finally:
        conn.close()