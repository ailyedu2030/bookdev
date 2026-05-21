"""
Project Schemas
"""

from pydantic import BaseModel, Field


# Project status literals - externalized enum
class ProjectStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    ALL = (DRAFT, ACTIVE, COMPLETED, ARCHIVED)

    @classmethod
    def pattern(cls) -> str:
        """Returns regex pattern for all statuses"""
        return "^(" + "|".join(cls.ALL) + ")$"


# Project member role literals
class ProjectMemberRole:
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    AUTHOR = "author"
    VIEWER = "viewer"

    ALL = (OWNER, EDITOR, REVIEWER, AUTHOR, VIEWER)

    @classmethod
    def pattern(cls) -> str:
        """Returns regex pattern for all roles"""
        return "^(" + "|".join(cls.ALL) + ")$"


# Default values
DEFAULT_TOTAL_CHAPTERS = 0
DEFAULT_PROGRESS = 0

# Field length constraints
NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000


class ProjectCreate(BaseModel):
    """Project creation schema"""

    name: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    total_chapters: int | None = Field(default=DEFAULT_TOTAL_CHAPTERS, ge=0)


class ProjectUpdate(BaseModel):
    """Project update schema"""

    name: str | None = Field(default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: str | None = Field(default=None, pattern=ProjectStatus.pattern())


class ProjectResponse(BaseModel):
    """Project response schema"""

    id: str
    name: str
    description: str | None = None
    status: str
    owner_id: str | None = None
    total_chapters: int = DEFAULT_TOTAL_CHAPTERS
    current_progress: int = DEFAULT_PROGRESS
    created_at: str
    updated_at: str | None = None


class ProjectMemberAdd(BaseModel):
    """Project member addition schema"""

    user_id: str
    role: str = Field(..., pattern=ProjectMemberRole.pattern())


class ProjectMemberResponse(BaseModel):
    """Project member response schema"""

    project_id: str
    user_id: str
    role: str
    assigned_at: str
    user: dict | None = None


class ProjectListResponse(BaseModel):
    """Project list response with pagination"""

    success: bool = True
    data: list[ProjectResponse]
    meta: dict = Field(default_factory=lambda: {"total": 0, "page": 1, "per_page": 20, "total_pages": 0})


class ProjectStats(BaseModel):
    """Project statistics"""

    total_chapters: int = Field(default=0, ge=0)
    completed_chapters: int = Field(default=0, ge=0)
    in_progress_chapters: int = Field(default=0, ge=0)
    draft_chapters: int = Field(default=0, ge=0)
    total_words: int = Field(default=0, ge=0)
    reviewed_chapters: int = Field(default=0, ge=0)
    approved_chapters: int = Field(default=0, ge=0)
