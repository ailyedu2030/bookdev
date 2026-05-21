"""
Admin Routes

Handles user and system administration:
- GET /api/admin/users - List users
- POST /api/admin/users - Create user
- PUT /api/admin/users/{id} - Update user
- DELETE /api/admin/users/{id} - Delete user
- PUT /api/admin/users/{id}/role - Update user role
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import (
    ROLE_HIERARCHY,
    DatabaseSession,
    User,
    get_db,
    get_password_hash,
    require_role,
)
from api.middleware.csrf import csrf_protect
from api.schemas.auth import UserCreate, UserResponse, UserRoleUpdate, UserUpdate
from api.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    role_filter: str | None = Query(default=None),
    search: str | None = Query(default=None),
    user: User = Depends(require_role("system_admin", "content_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all users with pagination and filtering.

    - **page**: Page number
    - **per_page**: Items per page
    - **role_filter**: Filter by role
    - **search**: Search by username or email
    """
    all_users = list(db._users.values())

    if role_filter:
        all_users = [u for u in all_users if u.role == role_filter]

    if search:
        search_lower = search.lower()
        all_users = [
            u for u in all_users
            if search_lower in u.username.lower() or search_lower in u.email.lower()
        ]

    len(all_users)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            organization_id=u.organization_id,
            clearance_level=u.clearance_level,
            created_at=datetime.utcnow().isoformat(),
        )
        for u in all_users[start_idx:end_idx]
    ]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_user(
    user_data: UserCreate,
    user: User = Depends(require_role("system_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new user (admin only).

    - **username**: Unique username
    - **email**: Valid email address
    - **password**: Password (8-128 characters)
    - **role**: User role
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

    new_user = db.create_user({
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "role": user_data.role or "viewer",
        "organization_id": user_data.organization_id,
        "clearance_level": 1,
    })

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        organization_id=new_user.organization_id,
        clearance_level=new_user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.get("/users/{target_user_id}", response_model=UserResponse)
async def get_user(
    target_user_id: str,
    user: User = Depends(require_role("system_admin", "content_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get user details by ID.
    """
    target_user = db.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                }
            },
        )

    return UserResponse(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        role=target_user.role,
        organization_id=target_user.organization_id,
        clearance_level=target_user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.put(
    "/users/{target_user_id}",
    response_model=UserResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_user(
    target_user_id: str,
    update_data: UserUpdate,
    user: User = Depends(require_role("system_admin", "content_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update user details.

    Only system_admin can update any user.
    content_admin can update roles below their level.
    """
    target_user = db.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                }
            },
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_UPDATE_DATA",
                    "message": "No update data provided",
                }
            },
        )

    sensitive_fields = {"organization_id", "clearance_level"}
    if any(field in update_dict for field in sensitive_fields):
        if user.role != "system_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": "Only system_admin can modify organization_id or clearance_level",
                    }
                },
            )

    if "organization_id" in update_dict:
        target_user.organization_id = update_dict["organization_id"]
    if "clearance_level" in update_dict:
        target_user.clearance_level = update_dict["clearance_level"]

    return UserResponse(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        role=target_user.role,
        organization_id=target_user.organization_id,
        clearance_level=target_user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.delete(
    "/users/{target_user_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_user(
    target_user_id: str,
    user: User = Depends(require_role("system_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete a user (system_admin only).
    """
    if target_user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CANNOT_DELETE_SELF",
                    "message": "Cannot delete your own account",
                }
            },
        )

    target_user = db.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                }
            },
        )

    if target_user_id in db._users:
        db.delete_user(target_user_id)

    return SuccessResponse(
        success=True,
        message="User deleted successfully",
    )


@router.put(
    "/users/{target_user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_user_role(
    target_user_id: str,
    role_update: UserRoleUpdate,
    user: User = Depends(require_role("system_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update user's role (system_admin only).

    - **role**: New role (system_admin, content_admin, editor, reviewer, author, viewer)
    """
    target_user = db.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                }
            },
        )

    if target_user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CANNOT_MODIFY_OWN_ROLE",
                    "message": "Cannot modify your own role",
                }
            },
        )

    requester_level = ROLE_HIERARCHY.get(user.role, 0)
    target_level = ROLE_HIERARCHY.get(target_user.role, 0)
    new_level = ROLE_HIERARCHY.get(role_update.role, 0)

    if target_level >= requester_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CANNOT_MODIFY_EQUAL_OR_HIGHER_ROLE",
                    "message": "Cannot modify users with equal or higher clearance level",
                }
            },
        )

    if new_level > requester_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CANNOT_ASSIGN_HIGHER_ROLE",
                    "message": "Cannot assign a role higher than your own",
                }
            },
        )

    target_user.role = role_update.role

    return UserResponse(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        role=target_user.role,
        organization_id=target_user.organization_id,
        clearance_level=target_user.clearance_level,
        created_at=datetime.utcnow().isoformat(),
    )


@router.get("/roles/list", response_model=list[dict])
async def list_roles(
    user: User = Depends(require_role("system_admin", "content_admin")),
):
    """
    List all available roles with their permissions.
    """
    from api.deps import ROLE_HIERARCHY, ROLE_PERMISSIONS

    roles = []
    for role_name, level in sorted(ROLE_HIERARCHY.items(), key=lambda x: x[1], reverse=True):
        roles.append({
            "name": role_name,
            "level": level,
            "permissions": list(ROLE_PERMISSIONS.get(role_name, [])),
        })

    return roles


@router.get("/permissions/list", response_model=dict)
async def list_permissions(
    user: User = Depends(require_role("system_admin", "content_admin")),
):
    """
    List all available permissions by resource.
    """
    all_permissions = set()
    from api.deps import ROLE_PERMISSIONS

    for permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(permissions)

    resources = {}
    for perm in all_permissions:
        if perm == "*:*":
            continue
        resource, action = perm.split(":")
        if resource not in resources:
            resources[resource] = []
        resources[resource].append(action)

    return {
        "success": True,
        "resources": resources,
    }


@router.get("/stats", response_model=dict)
async def get_admin_stats(
    user: User = Depends(require_role("system_admin", "content_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get system administration statistics.
    """
    total_users = len(db._users)
    total_projects = len(db._projects)
    total_chapters = len(db._chapters)
    total_terms = len(db._terms)

    users_by_role = {}
    for u in db._users.values():
        role = u.role
        users_by_role[role] = users_by_role.get(role, 0) + 1

    projects_by_status = {}
    for p in db._projects.values():
        status = p.get("status", "unknown")
        projects_by_status[status] = projects_by_status.get(status, 0) + 1

    chapters_by_status = {}
    for c in db._chapters.values():
        status = c.get("status", "unknown")
        chapters_by_status[status] = chapters_by_status.get(status, 0) + 1

    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "total_projects": total_projects,
            "total_chapters": total_chapters,
            "total_terms": total_terms,
            "users_by_role": users_by_role,
            "projects_by_status": projects_by_status,
            "chapters_by_status": chapters_by_status,
        },
    }
