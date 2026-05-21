"""
Chapter Schemas
"""

from pydantic import BaseModel, Field


# Chapter/section status literals - externalized enum
class ChapterStatus:
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"

    ALL = (DRAFT, GENERATING, REVIEWING, APPROVED, PUBLISHED, REJECTED)

    @classmethod
    def pattern(cls) -> str:
        """Returns regex pattern for all statuses"""
        return "^(" + "|".join(cls.ALL) + ")$"


# Default values
DEFAULT_WORD_COUNT = 0

# Field length constraints
TITLE_MIN_LENGTH = 1
TITLE_MAX_LENGTH = 200
CONTENT_HASH_LENGTH = 64  # SHA-256 hash


class ChapterCreate(BaseModel):
    """Chapter creation schema"""
    project_id: str
    title: str = Field(..., min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: int = Field(..., ge=0)
    parent_chapter_id: str | None = None


class ChapterUpdate(BaseModel):
    """Chapter update schema"""
    title: str | None = Field(default=None, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern=ChapterStatus.pattern())
    content: str | None = None
    content_hash: str | None = Field(default=None, max_length=CONTENT_HASH_LENGTH)


class ChapterResponse(BaseModel):
    """Chapter response schema"""
    id: str
    project_id: str
    title: str
    order_num: int
    status: str
    word_count: int = DEFAULT_WORD_COUNT
    version: str
    content_hash: str | None = None
    parent_chapter_id: str | None = None
    created_at: str
    updated_at: str | None = None


class ChapterContentResponse(BaseModel):
    """Chapter content response schema"""
    id: str
    chapter_id: str
    content: str | None = None
    version: str
    content_hash: str
    created_by: str | None = None
    created_at: str


class SectionCreate(BaseModel):
    """Section creation schema"""
    chapter_id: str
    title: str = Field(..., min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: int = Field(..., ge=0)
    parent_section_id: str | None = None


class SectionUpdate(BaseModel):
    """Section update schema"""
    title: str | None = Field(default=None, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern=ChapterStatus.pattern())
    content: str | None = None


class SectionResponse(BaseModel):
    """Section response schema"""
    id: str
    chapter_id: str
    title: str
    order_num: int
    status: str
    word_count: int = DEFAULT_WORD_COUNT
    parent_section_id: str | None = None
    created_at: str
    updated_at: str | None = None


class ReviewSubmit(BaseModel):
    """Review submission schema"""
    chapter_id: str
    comments: str | None = Field(default=None, max_length=2000)


class ReviewApprove(BaseModel):
    """Review approval schema"""
    chapter_id: str
    comments: str | None = Field(default=None, max_length=2000)


class ReviewReject(BaseModel):
    """Review rejection schema"""
    chapter_id: str
    comments: str = Field(..., min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    """Review response schema"""
    id: str
    chapter_id: str
    reviewer_id: str | None = None
    status: str
    comments: str | None = None
    reviewed_at: str


class ChapterGenerateRequest(BaseModel):
    """Chapter AI generation request"""
    chapter_id: str
    prompt: str | None = Field(default=None, max_length=5000)
    force_regenerate: bool = False


class ChapterGenerateResponse(BaseModel):
    """Chapter AI generation response"""
    success: bool = True
    chapter_id: str
    status: str
    content: str | None = None
    word_count: int = DEFAULT_WORD_COUNT
    generation_id: str | None = None


class ChapterListResponse(BaseModel):
    """Chapter list response with pagination"""
    success: bool = True
    data: list[ChapterResponse]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "page": 1,
            "per_page": 20,
            "total_pages": 0
        }
    )


class ContentVersionResponse(BaseModel):
    """Content version response schema"""
    id: str
    chapter_id: str
    version: str
    content_hash: str
    merkle_root: str | None = None
    change_reason: str | None = None
    created_by: str | None = None
    created_at: str
