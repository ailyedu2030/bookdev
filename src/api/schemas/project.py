"""
Project Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Project creation schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    total_chapters: Optional[int] = Field(default=0, ge=0)


class ProjectUpdate(BaseModel):
    """Project update schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=None, pattern="^(draft|active|completed|archived)$")


class ProjectResponse(BaseModel):
    """Project response schema"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    owner_id: Optional[str] = None
    total_chapters: int = 0
    current_progress: int = 0
    created_at: str
    updated_at: Optional[str] = None


class ProjectMemberAdd(BaseModel):
    """Project member addition schema"""
    user_id: str
    role: str = Field(
        ...,
        pattern="^(owner|editor|reviewer|author|viewer)$"
    )


class ProjectMemberResponse(BaseModel):
    """Project member response schema"""
    project_id: str
    user_id: str
    role: str
    assigned_at: str
    user: Optional[dict] = None


class ProjectListResponse(BaseModel):
    """Project list response with pagination"""
    success: bool = True
    data: List[ProjectResponse]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "page": 1,
            "per_page": 20,
            "total_pages": 0
        }
    )


class ProjectStats(BaseModel):
    """Project statistics"""
    total_chapters: int
    completed_chapters: int
    in_progress_chapters: int
    draft_chapters: int
    total_words: int
    reviewed_chapters: int
    approved_chapters: int
