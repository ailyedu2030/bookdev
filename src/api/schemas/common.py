"""
Common API Schemas
"""

from datetime import datetime
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    success: bool = True
    data: List[T]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "page": 1,
            "per_page": 20,
            "total_pages": 0
        }
    )
    links: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: dict = Field(
        default_factory=lambda: {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred"
        }
    )


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    components: Optional[dict] = None
    version: str = "1.0.0"


class MetricsResponse(BaseModel):
    """Metrics response"""
    success: bool = True
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class LogEntry(BaseModel):
    """Log entry response"""
    id: str
    event_type: str
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: str


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class IDParams(BaseModel):
    """Common path parameters for ID"""
    id: str


class ProjectIDParams(BaseModel):
    """Project ID path parameter"""
    project_id: str


class ChapterIDParams(BaseModel):
    """Chapter ID path parameter"""
    id: str


class ScanRequest(BaseModel):
    """Content scan request"""
    content: str
    categories: Optional[List[str]] = None


class ScanResponse(BaseModel):
    """Content scan response"""
    success: bool = True
    is_safe: bool
    confidence_score: float
    categories: List[str]
    violations: List[dict]
    action: str
    details: str


class DOIVerifyRequest(BaseModel):
    """DOI verification request"""
    doi: str


class DOIVerifyResponse(BaseModel):
    """DOI verification response"""
    success: bool = True
    valid: bool
    doi: str
    metadata: Optional[dict] = None
    error: Optional[str] = None


class RegulationVerifyRequest(BaseModel):
    """Regulation verification request"""
    content: str
    law_type: Optional[str] = None


class RegulationVerifyResponse(BaseModel):
    """Regulation verification response"""
    success: bool = True
    valid: bool
    matched_laws: List[dict]
    confidence: float
    details: str


class SemanticScanRequest(BaseModel):
    """Semantic scan request"""
    content: str
    threshold: float = Field(default=0.7, ge=0, le=1)


class SemanticScanResponse(BaseModel):
    """Semantic scan response"""
    success: bool = True
    issues: List[dict]
    score: float
    summary: str
