"""
Family management API endpoints
"""
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..schemas.family import FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse

router = APIRouter(prefix="/family", tags=["family"])


def get_current_user_dependency(authorization: str = Header(None)):
    """FastAPI dependency for user authentication"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    user_data = AuthService.verify_user_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        'sub': user_data['id'],
        'id': user_data['id'],
        'email': user_data['email'],
        'name': user_data['name'],
        'is_admin': user_data['is_admin']
    }


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    user_data = AuthService.verify_user_token(token)
    if user_data:
        return {
            'sub': user_data['id'],
            'id': user_data['id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'is_admin': user_data['is_admin']
        }
    return None


@router.get("/members", response_model=List[FamilyMemberResponse])
async def get_family_members(authorization: str = Header(None)):
    """Get family members for the authenticated user"""
    # Try to get current user, with admin fallback
    current_user = get_current_user(authorization)
    
    if not current_user:
        # Admin fallback - check for admin credentials in environment
        import os
        admin_email = os.getenv("ADMIN_EMAIL", "admin@foodplanning.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        # For now, just require authentication
        raise HTTPException(status_code=401, detail="Authentication required")
    
    with get_db_session() as session:
        if current_user.get("is_admin", False):
            # Admin can see all family members
            session.execute('''
                SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at 
                FROM family_members
                ORDER BY created_at DESC
            ''')
        else:
            # Regular users only see their own family members
            session.execute('''
                SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at 
                FROM family_members 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (current_user["sub"],))
        
        rows = session.fetchall()
        family_members = []
        
        for row in rows:
            # Parse dietary_restrictions and preferences from JSON strings
            try:
                dietary_restrictions = json.loads(row[4]) if row[4] else []
            except (json.JSONDecodeError, TypeError):
                dietary_restrictions = []
            
            try:
                preferences = json.loads(row[5]) if row[5] else {}
            except (json.JSONDecodeError, TypeError):
                preferences = {}
            
            family_member = FamilyMemberResponse(
                id=row[0],
                user_id=row[1],
                name=row[2],
                age=row[3],
                dietary_restrictions=dietary_restrictions,
                preferences=preferences,
                created_at=row[6]
            )
            family_members.append(family_member)
        
        return family_members


@router.post("/members", response_model=FamilyMemberResponse)
async def create_family_member(
    member_data: FamilyMemberCreate, 
    current_user: dict = Depends(get_current_user_dependency)
):
    """Create a new family member"""
    with get_db_session() as session:
        member_id = str(uuid.uuid4())
        
        # Serialize dietary_restrictions and preferences as JSON
        dietary_restrictions_str = json.dumps(member_data.dietary_restrictions or [])
        preferences_str = json.dumps(member_data.preferences or {})
        
        session.execute('''
            INSERT INTO family_members (id, user_id, name, age, dietary_restrictions, preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            member_id,
            current_user["sub"],
            member_data.name,
            member_data.age,
            dietary_restrictions_str,
            preferences_str
        ))
        
        # Fetch the created family member
        session.execute('''
            SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at 
            FROM family_members 
            WHERE id = ?
        ''', (member_id,))
        
        row = session.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create family member")
        
        # Parse the stored data
        try:
            dietary_restrictions = json.loads(row[4]) if row[4] else []
        except (json.JSONDecodeError, TypeError):
            dietary_restrictions = []
        
        try:
            preferences = json.loads(row[5]) if row[5] else {}
        except (json.JSONDecodeError, TypeError):
            preferences = {}
        
        return FamilyMemberResponse(
            id=row[0],
            user_id=row[1],
            name=row[2],
            age=row[3],
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
            created_at=row[6]
        )


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: str, 
    member_data: FamilyMemberUpdate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Update an existing family member"""
    with get_db_session() as session:
        # First check if the family member exists and belongs to the user
        session.execute('''
            SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at 
            FROM family_members 
            WHERE id = ?
        ''', (member_id,))
        
        existing_member = session.fetchone()
        if not existing_member:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        # Check ownership (unless admin)
        if not current_user.get("is_admin", False) and existing_member[1] != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        if member_data.name is not None:
            update_fields.append("name = ?")
            update_values.append(member_data.name)
        
        if member_data.age is not None:
            update_fields.append("age = ?")
            update_values.append(member_data.age)
        
        if member_data.dietary_restrictions is not None:
            update_fields.append("dietary_restrictions = ?")
            update_values.append(json.dumps(member_data.dietary_restrictions))
        
        if member_data.preferences is not None:
            update_fields.append("preferences = ?")
            update_values.append(json.dumps(member_data.preferences))
        
        if not update_fields:
            # No fields to update, return current data
            pass
        else:
            # Perform the update
            update_query = f"UPDATE family_members SET {', '.join(update_fields)} WHERE id = ?"
            update_values.append(member_id)
            
            session.execute(update_query, update_values)
        
        # Fetch updated family member
        session.execute('''
            SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at 
            FROM family_members 
            WHERE id = ?
        ''', (member_id,))
        
        row = session.fetchone()
        
        # Parse the stored data
        try:
            dietary_restrictions = json.loads(row[4]) if row[4] else []
        except (json.JSONDecodeError, TypeError):
            dietary_restrictions = []
        
        try:
            preferences = json.loads(row[5]) if row[5] else {}
        except (json.JSONDecodeError, TypeError):
            preferences = {}
        
        return FamilyMemberResponse(
            id=row[0],
            user_id=row[1],
            name=row[2],
            age=row[3],
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
            created_at=row[6]
        )


@router.delete("/members/{member_id}")
async def delete_family_member(
    member_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Delete a family member"""
    with get_db_session() as session:
        # Check if family member exists and belongs to user
        session.execute('''
            SELECT user_id FROM family_members WHERE id = ?
        ''', (member_id,))
        
        result = session.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        # Check ownership (unless admin)
        if not current_user.get("is_admin", False) and result[0] != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the family member
        session.execute('DELETE FROM family_members WHERE id = ?', (member_id,))
        
        return {"message": "Family member deleted successfully"}