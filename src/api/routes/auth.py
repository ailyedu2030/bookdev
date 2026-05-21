"""
Authentication Routes

Handles user authentication:
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- POST /api/auth/refresh - Refresh token
- POST /api/auth/logout - Logout
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from api.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    PasswordChange,
)
from api.schemas.common import SuccessResponse
from api.deps import (
    get_db,
    get_current_active_user,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    DatabaseSession,
    User,
    generate_uuid,
)
from jose import JWTError
from api.middleware.rate_limit import RateLimitConfig, rate_limit
from api.middleware.csrf import csrf_protect

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(RateLimitConfig(
        requests=3,
        window_seconds=3600,
        key_prefix="register"
    )))],
)
async def register(
    user_data: UserCreate,
    db: DatabaseSession = Depends(get_db),
):
    """
    Register a new user.

    - **username**: Unique username (3-100 characters)
    - **email**: Valid email address
    - **password**: Password (8-128 characters)
    - **role**: User role (default: viewer)
    """
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "EMAIL_EXISTS",
                    "message": "A user with this email already exists",
                }
            },
        )

    # API-SEC-009: Validate role during registration
    valid_roles = {"viewer", "author", "reviewer", "editor", "content_admin", "system_admin"}
    if user_data.role and user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_ROLE",
                    "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}",
                }
            },
        )

    user = db.create_user({
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "role": user_data.role,
        "organization_id": user_data.organization_id,
        "clearance_level": 1,
    })

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        clearance_level=user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit(RateLimitConfig(
        requests=5,
        window_seconds=60,
        key_prefix="login"
    )))],
)
async def login(
    credentials: UserLogin,
    db: DatabaseSession = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access token and refresh token.
    """
    user = db.get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                }
            },
        )
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                }
            },
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                }
            },
        )

    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })

    refresh_token = create_refresh_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })

    db.add_session(user.id, access_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DatabaseSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token
    """
    try:
        token_data = decode_token(request.refresh_token, "refresh")

        user = db.get_user_by_id(token_data.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User no longer exists",
                    }
                },
            )

        new_access_token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        })

        new_refresh_token = create_refresh_token({
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        })

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_INVALID",
                    "message": "Invalid refresh token",
                }
            },
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def logout(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    Logout current user.

    Invalidates the current session.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if token in db._sessions:
            del db._sessions[token]

    return SuccessResponse(
        success=True,
        message="Logged out successfully",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get current authenticated user's information.
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        clearance_level=user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.post(
    "/password/change",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def change_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    Change current user's password.

    - **old_password**: Current password
    - **new_password**: New password (8-128 characters)
    """
    hash_to_check = user.password_hash or ""
    if not verify_password(password_data.old_password, hash_to_check):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INCORRECT_PASSWORD",
                    "message": "Current password is incorrect",
                }
            },
        )

    db.update_user(user.id, {
        "password_hash": get_password_hash(password_data.new_password)
    })

    return SuccessResponse(
        success=True,
        message="Password changed successfully",
    )


@router.post("/csrf-token", response_model=SuccessResponse)
async def get_csrf_token(
    request: Request,
    user: Optional[User] = Depends(get_current_active_user),
):
    """
    Get CSRF token for state-changing operations.

    Returns a CSRF token in the response cookie.
    """
    from api.middleware.csrf import csrf_token_manager

    token = csrf_token_manager.generate_token()

    response = JSONResponse(
        content={
            "success": True,
            "message": "CSRF token generated",
        }
    )

    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=True,
        samesite="strict",
        max_age=3600,
    )

    return response
