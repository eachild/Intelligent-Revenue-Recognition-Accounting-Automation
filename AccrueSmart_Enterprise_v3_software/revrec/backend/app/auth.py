# backend/app/auth.py
from __future__ import annotations
from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, Depends, Header
import os

# Simple token-based auth for development
# In production, use OAuth2, JWT, etc.
VALID_API_KEYS = set(os.getenv("API_KEYS", "dev-key-12345").split(","))

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and validate user from authorization header.
    In development mode, returns a mock user if no auth provided.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Development mode - allow unauthenticated access
    if os.getenv("ENV") == "development" or os.getenv("DISABLE_AUTH") == "true":
        return {
            "user_id": "dev-user",
            "email": "dev@example.com",
            "roles": ["admin", "auditor", "finance"],
            "permissions": ["*"]  # All permissions in dev mode
        }
    
    # Production mode - require valid token
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Validate token (simplified - in production use JWT verification)
    if token not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info (in production, decode from JWT or query database)
    return {
        "user_id": "user-123",
        "email": "user@example.com",
        "roles": ["auditor", "finance"],
        "permissions": ["reports.memo", "leases.export", "revrec.export"]
    }


def require(
    perms: Optional[List[str]] = None,
    any_of: Optional[List[str]] = None,
    roles: Optional[List[str]] = None
):
    """
    Decorator to require specific permissions or roles for an endpoint.
    
    Args:
        perms: List of permissions that ALL must be present (AND logic)
        any_of: List of permissions where at least ONE must be present (OR logic)
        roles: List of roles where at least ONE must be present
        
    Usage:
        @app.get("/admin")
        @require(perms=["admin.access"])
        def admin_endpoint():
            return {"message": "Admin only"}
            
        @app.get("/reports")
        @require(any_of=["reports.view", "reports.edit"])
        def reports_endpoint():
            return {"message": "Can view or edit reports"}
            
        @app.get("/finance")
        @require(roles=["finance", "admin"])
        def finance_endpoint():
            return {"message": "Finance or admin role required"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependency injection
            user = None
            
            # Try to get user from kwargs (if Depends was used)
            if "current_user" in kwargs:
                user = kwargs.pop("current_user")
            elif "user" in kwargs:
                user = kwargs.pop("user")
            else:
                # Try to get from Depends in function signature
                # This is a fallback - ideally use Depends(get_current_user)
                try:
                    user = get_current_user()
                except Exception:
                    # In development mode without auth
                    user = {
                        "user_id": "dev-user",
                        "permissions": ["*"],
                        "roles": ["admin"]
                    }
            
            # Check permissions
            user_perms = set(user.get("permissions", []))
            user_roles = set(user.get("roles", []))
            
            # Wildcard permission grants everything
            if "*" in user_perms:
                return await func(*args, **kwargs) if callable(func) and hasattr(func, '__code__') else func(*args, **kwargs)
            
            # Check required permissions (ALL must be present)
            if perms:
                missing = set(perms) - user_perms
                if missing:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Missing required permissions: {', '.join(missing)}"
                    )
            
            # Check any_of permissions (at least ONE must be present)
            if any_of:
                if not any(p in user_perms for p in any_of):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Requires at least one of: {', '.join(any_of)}"
                    )
            
            # Check roles (at least ONE must be present)
            if roles:
                if not any(r in user_roles for r in roles):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Requires at least one role: {', '.join(roles)}"
                    )
            
            # All checks passed - execute the function
            return await func(*args, **kwargs) if callable(func) and hasattr(func, '__code__') else func(*args, **kwargs)
        
        return wrapper
    return decorator


# Shorthand decorators for common use cases
def require_admin(func: Callable) -> Callable:
    """Shorthand for @require(roles=["admin"])"""
    return require(roles=["admin"])(func)


def require_finance(func: Callable) -> Callable:
    """Shorthand for @require(roles=["finance", "admin"])"""
    return require(roles=["finance", "admin"])(func)


def require_auditor(func: Callable) -> Callable:
    """Shorthand for @require(roles=["auditor", "admin"])"""
    return require(roles=["auditor", "admin"])(func)