"""
Chapter Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChapterCreate(BaseModel):
    """Chapter creation schema"""
    project_id: str
    title: str = Field(..., min_length=1, max_length=200)
    order_num: int = Field(..., ge=0)
    parent_chapter_id: Optional[str] = None


class ChapterUpdate(BaseModel):
    """Chapter update schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    order_num: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(
        default=None,
        pattern="^(draft|generating|reviewing|approved|published|rejected)$"
    )
    content: Optional[str] = None
    content_hash: Optional[str] = None


class ChapterResponse(BaseModel):
    """Chapter response schema"""
    id: str
    project_id: str
    title: str
    order_num: int
    status: str
    word_count: int = 0
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
    title: str = Field(..., min_length=1, max_length=200)
    order_num: int = Field(..., ge=0)
    parent_section_id: Optional[str] = None


class SectionUpdate(BaseModel):
    """Section update schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    order_num: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(
        default=None,
        pattern="^(draft|generating|reviewing|approved|published|rejected)$"
    )
    content: Optional[str] = None


class SectionResponse(BaseModel):
    """Section response schema"""
    id: str
    chapter_id: str
    title: str
    order_num: int
    status: str
    word_count: int = 0
    parent_section_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ReviewSubmit(BaseModel):
    """Review submission schema"""
    chapter_id: str
    comments: Optional[str] = None


class ReviewApprove(BaseModel):
    """Review approval schema"""
    chapter_id: str
    comments: Optional[str] = None


class ReviewReject(BaseModel):
    """Review rejection schema"""
    chapter_id: str
    comments: str = Field(..., min_length=1)


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
    prompt: Optional[str] = None
    force_regenerate: bool = False


class ChapterGenerateResponse(BaseModel):
    """Chapter AI generation response"""
    success: bool = True
    chapter_id: str
    status: str
    content: Optional[str] = None
    word_count: int = 0
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
