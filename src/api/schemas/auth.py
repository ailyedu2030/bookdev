"""
Authentication Schemas
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# User role literals - externalized enum values
class UserRole:
    SYSTEM_ADMIN = "system_admin"
    CONTENT_ADMIN = "content_admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    AUTHOR = "author"
    VIEWER = "viewer"

    ALL = (SYSTEM_ADMIN, CONTENT_ADMIN, EDITOR, REVIEWER, AUTHOR, VIEWER)

    @classmethod
    def pattern(cls) -> str:
        """Returns regex pattern for all roles"""
        return "^(" + "|".join(cls.ALL) + ")$"


# Token type literals
TokenType = Literal["bearer", "refresh", "access"]

# Token expiration defaults
ACCESS_TOKEN_EXPIRE_SECONDS = 1800  # 30 minutes
REFRESH_TOKEN_EXPIRE_SECONDS = 604800  # 7 days


class UserCreate(BaseModel):
    """User registration schema"""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str | None = Field(default=UserRole.VIEWER)
    organization_id: str | None = None


class UserLogin(BaseModel):
    """User login schema"""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User response schema"""

    id: str
    username: str
    email: str
    role: str
    organization_id: str | None = None
    clearance_level: int = Field(default=1, ge=1, le=5)
    created_at: str
    updated_at: str | None = None


class UserUpdate(BaseModel):
    """User update schema"""

    username: str | None = Field(default=None, min_length=3, max_length=100)
    email: EmailStr | None = None
    organization_id: str | None = None
    clearance_level: int | None = Field(default=None, ge=1, le=5)


class UserRoleUpdate(BaseModel):
    """User role update schema"""

    role: str = Field(..., pattern=UserRole.pattern())


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: TokenType = "bearer"
    expires_in: int = Field(default=ACCESS_TOKEN_EXPIRE_SECONDS, ge=1)


class TokenPayload(BaseModel):
    """JWT token payload"""

    sub: str
    email: str
    role: str
    exp: int
    iat: int
    type: TokenType = "access"


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str = Field(..., min_length=1)


class PasswordChange(BaseModel):
    """Password change schema"""

    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Password reset request"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirm schema"""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class RoleResponse(BaseModel):
    """Role response schema"""

    id: str
    name: str
    description: str | None = None
    created_at: str


class PermissionResponse(BaseModel):
    """Permission response schema"""

    id: str
    resource: str
    action: str
    description: str | None = None
