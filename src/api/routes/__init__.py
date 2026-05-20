"""
API Routes Package
"""

from api.routes.auth import router as auth_router
from api.routes.projects import router as projects_router
from api.routes.chapters import router as chapters_router
from api.routes.terms import router as terms_router
from api.routes.knowledge_graph import router as knowledge_graph_router
from api.routes.security import router as security_router
from api.routes.monitor import router as monitor_router
from api.routes.workflows import router as workflows_router
from api.routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "projects_router",
    "chapters_router",
    "terms_router",
    "knowledge_graph_router",
    "security_router",
    "monitor_router",
    "workflows_router",
    "admin_router",
]
