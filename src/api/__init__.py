"""
AI多Agent教材编写系统 - FastAPI API层

提供完整的REST API接口，包括：
- 认证 (JWT tokens, RBAC)
- 项目管理
- 章节管理
- 术语和概念管理
- 知识图谱
- 安全扫描
- 监控
- 工作流
- 系统管理
"""

__version__ = "1.0.0"

from api.deps import (
    DatabaseSession,
    User,
    get_current_active_user,
    get_current_user,
    get_db,
    get_optional_user,
    require_min_role,
    require_permission,
    require_role,
)
from api.router import api_router
from api.schemas import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ScanRequest,
    ScanResponse,
    SuccessResponse,
    TermCreate,
    TermResponse,
    TermUpdate,
    Token,
    UserCreate,
    UserLogin,
)

__all__ = [
    # Version
    "__version__",
    # Router
    "api_router",
    # Dependencies
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_permission",
    "require_role",
    "require_min_role",
    "User",
    "DatabaseSession",
    # Schemas
    "UserCreate",
    "UserLogin",
    "Token",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "TermCreate",
    "TermUpdate",
    "TermResponse",
    "ScanRequest",
    "ScanResponse",
    "HealthResponse",
    "MetricsResponse",
    "SuccessResponse",
    "ErrorResponse",
]
