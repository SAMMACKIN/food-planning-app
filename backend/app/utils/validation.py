"""
Validation utilities for the application
"""
import uuid
from typing import Any


def is_valid_uuid(val: Any) -> bool:
    """
    Check if a value is a valid UUID
    
    Args:
        val: Value to check
        
    Returns:
        bool: True if valid UUID, False otherwise
    """
    if not val:
        return False
    
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def validate_uuid_or_raise(val: Any, field_name: str = "ID") -> str:
    """
    Validate UUID and raise HTTPException if invalid
    
    Args:
        val: Value to validate
        field_name: Name of the field for error message
        
    Returns:
        str: Valid UUID string
        
    Raises:
        HTTPException: If UUID is invalid
    """
    from fastapi import HTTPException
    
    if not is_valid_uuid(val):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: must be a valid UUID")
    
    return str(val)


def validate_non_empty_string(val: Any, field_name: str) -> str:
    """
    Validate that a value is a non-empty string
    
    Args:
        val: Value to validate
        field_name: Name of the field for error message
        
    Returns:
        str: Valid string
        
    Raises:
        HTTPException: If string is empty or invalid
    """
    from fastapi import HTTPException
    
    if not val or not isinstance(val, str) or not val.strip():
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")
    
    return val.strip()