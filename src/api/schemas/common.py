"""
Common API Schemas
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, Optional, List, Literal
from pydantic import BaseModel, Field

# Default pagination values
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100

# API Version
API_VERSION = "1.0.0"

# Sort order literals
SortOrder = Literal["asc", "desc"]

# Error codes
class ErrorCode:
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

# Error detail structure
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[dict]] = None


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    success: bool = True
    data: List[T]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "page": DEFAULT_PAGE,
            "per_page": DEFAULT_PER_PAGE,
            "total_pages": 0
        }
    )
    links: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: ErrorDetail = Field(
        default_factory=lambda: ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred"
        )
    )


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    components: Optional[dict] = None
    version: str = API_VERSION


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
    page: int = Field(default=DEFAULT_PAGE, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)
    sort_by: Optional[str] = None
    sort_order: SortOrder = Field(default="desc")


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
    content: Optional[str] = Field(default="")
    categories: Optional[List[str]] = None


class ScanResponse(BaseModel):
    """Content scan response"""
    success: bool = True
    is_safe: bool
    confidence_score: float = Field(..., ge=0, le=1)
    categories: List[str] = Field(default_factory=list)
    violations: List[dict] = Field(default_factory=list)
    action: str
    details: str


class DOIVerifyRequest(BaseModel):
    """DOI verification request"""
    doi: str = Field(..., min_length=1, max_length=255)


class DOIVerifyResponse(BaseModel):
    """DOI verification response"""
    success: bool = True
    valid: bool
    doi: str
    metadata: Optional[dict] = None
    error: Optional[str] = None


class RegulationVerifyRequest(BaseModel):
    """Regulation verification request"""
    content: Optional[str] = Field(default="")
    law_type: Optional[str] = Field(default=None, max_length=50)


class RegulationVerifyResponse(BaseModel):
    """Regulation verification response"""
    success: bool = True
    valid: bool
    matched_laws: List[dict] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    details: str


class SemanticScanRequest(BaseModel):
    """Semantic scan request"""
    content: Optional[str] = Field(default="")
    threshold: float = Field(default=0.7, ge=0, le=1)


class SemanticScanResponse(BaseModel):
    """Semantic scan response"""
    success: bool = True
    issues: List[dict] = Field(default_factory=list)
    score: float = Field(..., ge=0, le=1)
    summary: str


class ConceptVerifyRequest(BaseModel):
    """Concept integrity verification request"""
    concept_id: str
    definition: str


class BatchScanRequest(BaseModel):
    """Batch scan request"""
    contents: List[str] = Field(default_factory=list)
