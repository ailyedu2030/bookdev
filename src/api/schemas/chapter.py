"""
Chapter Schemas
"""

from datetime import datetime, timezone
from typing import Optional, List, Literal
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
    parent_chapter_id: Optional[str] = None


class ChapterUpdate(BaseModel):
    """Chapter update schema"""
    title: Optional[str] = Field(default=None, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, pattern=ChapterStatus.pattern())
    content: Optional[str] = None
    content_hash: Optional[str] = Field(default=None, max_length=CONTENT_HASH_LENGTH)


class ChapterResponse(BaseModel):
    """Chapter response schema"""
    id: str
    project_id: str
    title: str
    order_num: int
    status: str
    word_count: int = DEFAULT_WORD_COUNT
    version: str
    content_hash: Optional[str] = None
    parent_chapter_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ChapterContentResponse(BaseModel):
    """Chapter content response schema"""
    id: str
    chapter_id: str
    content: Optional[str] = None
    version: str
    content_hash: str
    created_by: Optional[str] = None
    created_at: str


class SectionCreate(BaseModel):
    """Section creation schema"""
    chapter_id: str
    title: str = Field(..., min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: int = Field(..., ge=0)
    parent_section_id: Optional[str] = None


class SectionUpdate(BaseModel):
    """Section update schema"""
    title: Optional[str] = Field(default=None, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    order_num: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, pattern=ChapterStatus.pattern())
    content: Optional[str] = None


class SectionResponse(BaseModel):
    """Section response schema"""
    id: str
    chapter_id: str
    title: str
    order_num: int
    status: str
    word_count: int = DEFAULT_WORD_COUNT
    parent_section_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ReviewSubmit(BaseModel):
    """Review submission schema"""
    chapter_id: str
    comments: Optional[str] = Field(default=None, max_length=2000)


class ReviewApprove(BaseModel):
    """Review approval schema"""
    chapter_id: str
    comments: Optional[str] = Field(default=None, max_length=2000)


class ReviewReject(BaseModel):
    """Review rejection schema"""
    chapter_id: str
    comments: str = Field(..., min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    """Review response schema"""
    id: str
    chapter_id: str
    reviewer_id: Optional[str] = None
    status: str
    comments: Optional[str] = None
    reviewed_at: str


class ChapterGenerateRequest(BaseModel):
    """Chapter AI generation request"""
    chapter_id: str
    prompt: Optional[str] = Field(default=None, max_length=5000)
    force_regenerate: bool = False


class ChapterGenerateResponse(BaseModel):
    """Chapter AI generation response"""
    success: bool = True
    chapter_id: str
    status: str
    content: Optional[str] = None
    word_count: int = DEFAULT_WORD_COUNT
    generation_id: Optional[str] = None


class ChapterListResponse(BaseModel):
    """Chapter list response with pagination"""
    success: bool = True
    data: List[ChapterResponse]
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
    merkle_root: Optional[str] = None
    change_reason: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str
