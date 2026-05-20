"""
Authentication Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """User registration schema"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(default="viewer")
    organization_id: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    username: str
    email: str
    role: str
    organization_id: Optional[str] = None
    clearance_level: int = 1
    created_at: str
    updated_at: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    organization_id: Optional[str] = None
    clearance_level: Optional[int] = Field(default=None, ge=1, le=5)


class UserRoleUpdate(BaseModel):
    """User role update schema"""
    role: str = Field(..., pattern="^(system_admin|content_admin|editor|reviewer|author|viewer)$")


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str
    email: str
    role: str
    exp: int
    iat: int
    type: str = "access"


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirm schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class RoleResponse(BaseModel):
    """Role response schema"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str


class PermissionResponse(BaseModel):
    """Permission response schema"""
    id: str
    resource: str
    action: str
    description: Optional[str] = None
