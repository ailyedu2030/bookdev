"""
API Schemas Package
"""

from api.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenPayload,
    RefreshTokenRequest,
)
from api.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectMemberAdd,
    ProjectMemberResponse,
)
from api.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    ReviewSubmit,
    ReviewResponse,
)
from api.schemas.term import (
    TermCreate,
    TermUpdate,
    TermResponse,
)
from api.schemas.common import (
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    HealthResponse,
    MetricsResponse,
    LogEntry,
    PaginationParams,
    IDParams,
    ProjectIDParams,
    ChapterIDParams,
    ScanRequest,
    ScanResponse,
    DOIVerifyRequest,
    DOIVerifyResponse,
    RegulationVerifyRequest,
    RegulationVerifyResponse,
    SemanticScanRequest,
    SemanticScanResponse,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectMemberAdd",
    "ProjectMemberResponse",
    # Chapter
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "SectionCreate",
    "SectionUpdate",
    "SectionResponse",
    "ReviewSubmit",
    "ReviewResponse",
    # Term
    "TermCreate",
    "TermUpdate",
    "TermResponse",
    # Common
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "HealthResponse",
    "MetricsResponse",
    "LogEntry",
    "PaginationParams",
    "IDParams",
    "ProjectIDParams",
    "ChapterIDParams",
    "ScanRequest",
    "ScanResponse",
    "DOIVerifyRequest",
    "DOIVerifyResponse",
    "RegulationVerifyRequest",
    "RegulationVerifyResponse",
    "SemanticScanRequest",
    "SemanticScanResponse",
]
