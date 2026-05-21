"""
Chapter Management Routes

Handles chapter and section CRUD operations:
- GET /api/chapters/{project_id} - List chapters for a project
- POST /api/chapters - Create chapter
- GET /api/chapters/{id} - Get chapter details
- PUT /api/chapters/{id} - Update chapter
- DELETE /api/chapters/{id} - Delete chapter
- POST /api/chapters/{id}/generate - AI generate chapter content
- POST /api/chapters/{id}/review - Submit for review
- POST /api/chapters/{id}/approve - Approve chapter
- POST /api/chapters/{id}/reject - Reject chapter
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from api.deps import (
    DatabaseSession,
    User,
    generate_uuid,
    get_db,
    hash_content,
    require_permission,
    require_role,
)
from api.middleware.csrf import csrf_protect
from api.middleware.rate_limit import RateLimitConfig, rate_limit
from api.schemas.chapter import (
    ChapterCreate,
    ChapterGenerateRequest,
    ChapterGenerateResponse,
    ChapterListResponse,
    ChapterResponse,
    ChapterUpdate,
    ContentVersionResponse,
    ReviewApprove,
    ReviewReject,
    ReviewResponse,
    ReviewSubmit,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from api.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/chapters", tags=["Chapters"])


@router.get("/{project_id}", response_model=ChapterListResponse)
async def list_chapters(
    project_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None),
    user: User = Depends(require_permission("chapters:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all chapters for a project.

    - **project_id**: Project ID
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **status_filter**: Filter by status
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

    if status_filter:
        chapters = [c for c in chapters if c.get("status") == status_filter]

    total = len(chapters)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return ChapterListResponse(
        success=True,
        data=[ChapterResponse(**c) for c in chapters[start_idx:end_idx]],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post(
    "",
    response_model=ChapterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_chapter(
    chapter_data: ChapterCreate,
    user: User = Depends(require_permission("chapters:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new chapter.

    - **project_id**: Parent project ID
    - **title**: Chapter title
    - **order_num**: Chapter order number
    - **parent_chapter_id**: Optional parent chapter ID for nested chapters
    """
    project = db.get_project(chapter_data.project_id)
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

    chapter = db.create_chapter({
        "project_id": chapter_data.project_id,
        "title": chapter_data.title,
        "order_num": chapter_data.order_num,
        "parent_chapter_id": chapter_data.parent_chapter_id,
    })

    return ChapterResponse(**chapter)


@router.get("/detail/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    chapter_id: str,
    user: User = Depends(require_permission("chapters:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get chapter details by ID.
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    return ChapterResponse(**chapter)


@router.put(
    "/{chapter_id}",
    response_model=ChapterResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_chapter(
    chapter_id: str,
    update_data: ChapterUpdate,
    user: User = Depends(require_permission("chapters:update")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update chapter details.

    - **title**: New chapter title
    - **order_num**: New order number
    - **status**: New status
    - **content**: New content
    - **content_hash**: Content hash for integrity
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    if "content" in update_dict and update_dict["content"]:
        update_dict["content_hash"] = hash_content(update_dict["content"])
        update_dict["word_count"] = len(update_dict["content"])

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

    updated_chapter = db.update_chapter(chapter_id, update_dict)
    return ChapterResponse(**updated_chapter)


@router.delete(
    "/{chapter_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_chapter(
    chapter_id: str,
    user: User = Depends(require_permission("chapters:delete")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete a chapter.
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    db.delete_chapter(chapter_id)

    return SuccessResponse(
        success=True,
        message="Chapter deleted successfully",
    )


@router.post(
    "/{chapter_id}/generate",
    response_model=ChapterGenerateResponse,
    dependencies=[
        Depends(csrf_protect),
        Depends(rate_limit(RateLimitConfig(
            requests=10,
            window_seconds=3600,
            key_prefix="generate"
        ))),
    ],
)
async def generate_chapter_content(
    chapter_id: str,
    request: ChapterGenerateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission("chapters:generate")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Trigger AI content generation for a chapter.

    - **chapter_id**: Chapter ID to generate
    - **prompt**: Optional custom prompt
    - **force_regenerate**: Force regeneration even if content exists
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    generation_id = generate_uuid()

    db.update_chapter(chapter_id, {
        "status": "generating",
        "generation_id": generation_id,
    })

    background_tasks.add_task(
        simulate_content_generation,
        chapter_id,
        generation_id,
        request.prompt,
        user.id,
        db,
    )

    return ChapterGenerateResponse(
        success=True,
        chapter_id=chapter_id,
        status="generating",
        generation_id=generation_id,
    )


async def simulate_content_generation(
    chapter_id: str,
    generation_id: str,
    prompt: str,
    user_id: str,
    db: DatabaseSession,
):
    """Simulate background content generation"""
    import asyncio
    await asyncio.sleep(2)

    generated_content = f"Generated content for chapter {chapter_id}..."

    word_count = len(generated_content)

    db.update_chapter(chapter_id, {
        "content": generated_content,
        "status": "draft",
        "word_count": word_count,
        "content_hash": hash_content(generated_content),
        "version": "1.0",
    })


@router.post(
    "/{chapter_id}/review",
    response_model=ReviewResponse,
    dependencies=[Depends(csrf_protect)],
)
async def submit_for_review(
    chapter_id: str,
    review_data: ReviewSubmit,
    user: User = Depends(require_permission("chapters:submit")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Submit a chapter for review.

    - **chapter_id**: Chapter ID
    - **comments**: Optional review comments
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    db.update_chapter(chapter_id, {"status": "reviewing"})

    return ReviewResponse(
        id=generate_uuid(),
        chapter_id=chapter_id,
        reviewer_id=user.id,
        status="submitted",
        comments=review_data.comments,
        reviewed_at=datetime.utcnow().isoformat(),
    )


@router.post(
    "/{chapter_id}/approve",
    response_model=ReviewResponse,
    dependencies=[Depends(csrf_protect)],
)
async def approve_chapter(
    chapter_id: str,
    approval_data: ReviewApprove,
    user: User = Depends(require_role("reviewer", "content_admin", "system_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Approve a chapter.

    - **chapter_id**: Chapter ID
    - **comments**: Optional approval comments
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    db.update_chapter(chapter_id, {"status": "approved"})

    return ReviewResponse(
        id=generate_uuid(),
        chapter_id=chapter_id,
        reviewer_id=user.id,
        status="approved",
        comments=approval_data.comments,
        reviewed_at=datetime.utcnow().isoformat(),
    )


@router.post(
    "/{chapter_id}/reject",
    response_model=ReviewResponse,
    dependencies=[Depends(csrf_protect)],
)
async def reject_chapter(
    chapter_id: str,
    rejection_data: ReviewReject,
    user: User = Depends(require_role("reviewer", "content_admin", "system_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Reject a chapter.

    - **chapter_id**: Chapter ID
    - **comments**: Rejection reason (required)
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    db.update_chapter(chapter_id, {"status": "rejected"})

    return ReviewResponse(
        id=generate_uuid(),
        chapter_id=chapter_id,
        reviewer_id=user.id,
        status="rejected",
        comments=rejection_data.comments,
        reviewed_at=datetime.utcnow().isoformat(),
    )


@router.get("/{chapter_id}/versions", response_model=list[ContentVersionResponse])
async def list_content_versions(
    chapter_id: str,
    user: User = Depends(require_permission("chapters:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all content versions for a chapter.
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    return [
        ContentVersionResponse(
            id=generate_uuid(),
            chapter_id=chapter_id,
            version=chapter.get("version", "1.0"),
            content_hash=chapter.get("content_hash", ""),
            merkle_root=None,
            change_reason=None,
            created_by=user.id,
            created_at=chapter.get("updated_at", datetime.utcnow().isoformat()),
        )
    ]


@router.post(
    "/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_section(
    section_data: SectionCreate,
    user: User = Depends(require_permission("chapters:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new section within a chapter.

    - **chapter_id**: Parent chapter ID
    - **title**: Section title
    - **order_num**: Section order number
    - **parent_section_id**: Optional parent section ID for nested sections
    """
    chapter = db.get_chapter(section_data.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHAPTER_NOT_FOUND",
                    "message": "Chapter not found",
                }
            },
        )

    section = db.create_section({
        "chapter_id": section_data.chapter_id,
        "title": section_data.title,
        "order_num": section_data.order_num,
        "status": "draft",
        "parent_section_id": section_data.parent_section_id,
    })

    return SectionResponse(
        id=section["id"],
        chapter_id=section["chapter_id"],
        title=section["title"],
        order_num=section["order_num"],
        status=section["status"],
        word_count=section.get("word_count", 0),
        parent_section_id=section.get("parent_section_id"),
        created_at=section["created_at"],
    )


@router.put(
    "/sections/{section_id}",
    response_model=SectionResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_section(
    section_id: str,
    update_data: SectionUpdate,
    user: User = Depends(require_permission("chapters:update")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update a section.

    - **title**: New section title
    - **order_num**: New order number
    - **status**: New status
    - **content**: New content
    """
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

    existing = db.get_section(section_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SECTION_NOT_FOUND",
                    "message": "Section not found",
                }
            },
        )

    updated = db.update_section(section_id, update_dict)
    assert updated is not None, "update_section should not return None after existence check"

    return SectionResponse(
        id=updated["id"],
        chapter_id=updated["chapter_id"],
        title=updated["title"],
        order_num=updated["order_num"],
        status=updated["status"],
        word_count=updated.get("word_count", 0),
        parent_section_id=updated.get("parent_section_id"),
        created_at=updated["created_at"],
    )
