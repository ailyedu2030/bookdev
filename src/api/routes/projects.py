"""
Project Management Routes

Handles project CRUD operations:
- GET /api/projects - List projects
- POST /api/projects - Create project
- GET /api/projects/{id} - Get project details
- PUT /api/projects/{id} - Update project
- DELETE /api/projects/{id} - Delete project
- POST /api/projects/{id}/members - Add project member
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import (
    DatabaseSession,
    User,
    get_current_active_user,
    get_db,
    require_permission,
)
from api.middleware.csrf import csrf_protect
from api.schemas.common import SuccessResponse
from api.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None),
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all projects with pagination.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **status_filter**: Filter by status (draft, active, completed, archived)
    """
    all_projects = db.list_projects()

    if status_filter:
        all_projects = [p for p in all_projects if p.get("status") == status_filter]

    total = len(all_projects)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    projects = all_projects[start_idx:end_idx]

    return ProjectListResponse(
        success=True,
        data=[ProjectResponse(**p) for p in projects],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_project(
    project_data: ProjectCreate,
    user: User = Depends(require_permission("projects:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new project.

    - **name**: Project name (required)
    - **description**: Project description
    - **total_chapters**: Total expected chapters
    """
    project = db.create_project({
        "name": project_data.name,
        "description": project_data.description,
        "total_chapters": project_data.total_chapters,
        "owner_id": user.id,
    })

    return ProjectResponse(**project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(require_permission("projects:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get project details by ID.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project not found",
                }
            },
        )

    return ProjectResponse(**project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    user: User = Depends(require_permission("projects:update")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update project details.

    - **name**: New project name
    - **description**: New description
    - **status**: New status (draft, active, completed, archived)
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project not found",
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

    updated_project = db.update_project(project_id, update_dict)
    return ProjectResponse(**updated_project)


@router.delete(
    "/{project_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_project(
    project_id: str,
    user: User = Depends(require_permission("projects:delete")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete a project.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project not found",
                }
            },
        )

    if project.get("owner_id") != user.id and user.role != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "Only the owner can delete this project",
                }
            },
        )

    db.delete_project(project_id)

    return SuccessResponse(
        success=True,
        message="Project deleted successfully",
    )


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberAdd,
    user: User = Depends(require_permission("projects:manage_members")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Add a member to the project.

    - **user_id**: User ID to add
    - **role**: Role for the user (owner, editor, reviewer, author, viewer)
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project not found",
                }
            },
        )

    member_user = db.get_user_by_id(member_data.user_id)
    if not member_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                }
            },
        )

    return ProjectMemberResponse(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role,
        assigned_at=datetime.utcnow().isoformat(),
        user={
            "id": member_user.id,
            "username": member_user.username,
            "email": member_user.email,
        },
    )


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    user: User = Depends(require_permission("projects:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get project statistics.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project not found",
                }
            },
        )

    chapters = db.list_chapters_by_project(project_id)

    total_chapters = len(chapters)
    completed_chapters = len([c for c in chapters if c.get("status") == "published"])
    in_progress_chapters = len([c for c in chapters if c.get("status") in ("generating", "reviewing")])
    draft_chapters = len([c for c in chapters if c.get("status") == "draft"])
    reviewed_chapters = len([c for c in chapters if c.get("status") == "reviewing"])
    approved_chapters = len([c for c in chapters if c.get("status") == "approved"])
    total_words = sum(c.get("word_count", 0) for c in chapters)

    return ProjectStats(
        total_chapters=total_chapters,
        completed_chapters=completed_chapters,
        in_progress_chapters=in_progress_chapters,
        draft_chapters=draft_chapters,
        total_words=total_words,
        reviewed_chapters=reviewed_chapters,
        approved_chapters=approved_chapters,
    )


@router.get("/my/projects", response_model=ProjectListResponse)
async def list_my_projects(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List projects owned by or shared with the current user.
    """
    all_projects = db.list_projects(owner_id=user.id)

    total = len(all_projects)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    projects = all_projects[start_idx:end_idx]

    return ProjectListResponse(
        success=True,
        data=[ProjectResponse(**p) for p in projects],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )
