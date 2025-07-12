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
from ..models.family import FamilyMember
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
async def get_family_members(current_user: dict = Depends(get_current_user_dependency)):
    """Get family members for the authenticated user"""
    with get_db_session() as session:
        if current_user.get("is_admin", False):
            # Admin can see all family members
            family_members = session.query(FamilyMember).order_by(FamilyMember.created_at.desc()).all()
        else:
            # Regular users only see their own family members
            family_members = session.query(FamilyMember).filter(
                FamilyMember.user_id == current_user["id"]
            ).order_by(FamilyMember.created_at.desc()).all()
        
        return [
            FamilyMemberResponse(
                id=str(member.id),
                user_id=str(member.user_id),
                name=member.name,
                age=member.age,
                dietary_restrictions=getattr(member, 'dietary_restrictions', []) or [],
                preferences=member.preferences or {},
                created_at=member.created_at.isoformat()
            )
            for member in family_members
        ]


@router.post("/members", response_model=FamilyMemberResponse)
async def create_family_member(
    member_data: FamilyMemberCreate, 
    current_user: dict = Depends(get_current_user_dependency)
):
    """Create a new family member"""
    with get_db_session() as session:
        # Create new family member using SQLAlchemy model
        # Handle dietary_restrictions field gracefully for backward compatibility
        member_kwargs = {
            'id': uuid.uuid4(),
            'user_id': current_user["id"],  # Use 'id' instead of 'sub'
            'name': member_data.name,
            'age': member_data.age,
            'preferences': member_data.preferences or {}
        }
        
        # Only set dietary_restrictions if the column exists in the database
        try:
            if hasattr(member_data, 'dietary_restrictions') and member_data.dietary_restrictions is not None:
                member_kwargs['dietary_restrictions'] = member_data.dietary_restrictions
        except Exception:
            pass  # Column doesn't exist yet, skip it
            
        new_member = FamilyMember(**member_kwargs)
        
        session.add(new_member)
        session.commit()
        session.refresh(new_member)
        
        return FamilyMemberResponse(
            id=str(new_member.id),
            user_id=str(new_member.user_id),
            name=new_member.name,
            age=new_member.age,
            dietary_restrictions=getattr(new_member, 'dietary_restrictions', []) or [],
            preferences=new_member.preferences or {},
            created_at=new_member.created_at.isoformat()
        )


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: str, 
    member_data: FamilyMemberUpdate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Update an existing family member"""
    with get_db_session() as session:
        # Find the existing family member using SQLAlchemy
        existing_member = session.query(FamilyMember).filter(
            FamilyMember.id == member_id
        ).first()
        
        if not existing_member:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        # Check ownership (unless admin)
        # Convert current_user["id"] to UUID for comparison
        current_user_uuid = uuid.UUID(current_user["id"])
        if not current_user.get("is_admin", False) and existing_member.user_id != current_user_uuid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update fields that were provided
        if member_data.name is not None:
            existing_member.name = member_data.name
        
        if member_data.age is not None:
            existing_member.age = member_data.age
            
        # Only update dietary_restrictions if the column exists
        if member_data.dietary_restrictions is not None:
            try:
                if hasattr(existing_member, 'dietary_restrictions'):
                    existing_member.dietary_restrictions = member_data.dietary_restrictions
            except Exception:
                pass  # Column doesn't exist yet, skip it
        
        if member_data.preferences is not None:
            existing_member.preferences = member_data.preferences
        
        session.commit()
        session.refresh(existing_member)
        
        return FamilyMemberResponse(
            id=str(existing_member.id),
            user_id=str(existing_member.user_id),
            name=existing_member.name,
            age=existing_member.age,
            dietary_restrictions=getattr(existing_member, 'dietary_restrictions', []) or [],
            preferences=existing_member.preferences or {},
            created_at=existing_member.created_at.isoformat()
        )


@router.delete("/members/{member_id}")
async def delete_family_member(
    member_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Delete a family member"""
    with get_db_session() as session:
        # Find the family member using SQLAlchemy
        family_member = session.query(FamilyMember).filter(
            FamilyMember.id == member_id
        ).first()
        
        if not family_member:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        # Check ownership (unless admin)
        # Convert current_user["id"] to UUID for comparison
        current_user_uuid = uuid.UUID(current_user["id"])
        if not current_user.get("is_admin", False) and family_member.user_id != current_user_uuid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the family member
        session.delete(family_member)
        session.commit()
        
        return {"message": "Family member deleted successfully"}