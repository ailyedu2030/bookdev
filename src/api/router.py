"""
Main API Router

Combines all route modules into a single router.
"""

from fastapi import APIRouter

from api.routes.admin import router as admin_router
from api.routes.auth import router as auth_router
from api.routes.chapters import router as chapters_router
from api.routes.dashboard import router as dashboard_router
from api.routes.knowledge_graph import router as knowledge_graph_router
from api.routes.monitor import router as monitor_router
from api.routes.projects import router as projects_router
from api.routes.security import router as security_router
from api.routes.terms import citation_router, concept_router
from api.routes.terms import router as terms_router
from api.routes.workflows import router as workflows_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(chapters_router)
api_router.include_router(terms_router)
api_router.include_router(concept_router)
api_router.include_router(citation_router)
api_router.include_router(knowledge_graph_router)
api_router.include_router(security_router)
api_router.include_router(monitor_router)
api_router.include_router(workflows_router)
api_router.include_router(admin_router)
api_router.include_router(dashboard_router)
