"""
FastAPI Application Entry Point

AI多Agent教材编写系统 - Web API Server
"""

import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

sys.path.insert(0, os.path.dirname(__file__))

from api.router import api_router
from api.middleware.rate_limit import RateLimitMiddleware, RateLimitConfig
from api.middleware.security_headers import SecurityHeadersMiddleware, SecurityHeadersConfig
from api.middleware.csrf import CSRFMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("  AI多Agent教材编写系统 v1.0")
    print("  FastAPI API Server Starting...")
    print("=" * 60)

    try:
        from f01_immutable_log.immutable_log import ImmutableLog
        log = ImmutableLog()
        log.append("system_start", {"status": "online"})
        print("  [OK] Immutable Log")
    except ImportError:
        print("  [SKIP] Immutable Log (module not available)")

    try:
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        health = dashboard.get_health_status()
        print(f"  [OK] Monitoring Dashboard - Status: {health.status}")
    except ImportError:
        print("  [SKIP] Monitoring Dashboard (module not available)")

    try:
        from f31_minimax_client.minimax_client import MiniMaxClient
        print("  [OK] MiniMax Client")
    except ImportError:
        print("  [SKIP] MiniMax Client (module not available)")

    print("=" * 60)
    print("  API Server Ready!")
    print("  Docs: http://localhost:8000/docs")
    print("  Health: http://localhost:8000/api/monitor/health")
    print("=" * 60)

    yield

    print("\nShutting down API Server...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI多Agent教材编写系统",
        description="基于AI多智能体协同的教材编写系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "https://textbook.example.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-CSRF-Token"],
    )

    app.add_middleware(
        SecurityHeadersMiddleware,
        config=SecurityHeadersConfig(),
        exclude_paths=["/docs", "/redoc", "/openapi.json"],
    )

    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(requests=100, window_seconds=60),
        exempt_paths=["/api/monitor/health", "/docs", "/openapi.json"],
    )

    app.add_middleware(CSRFMiddleware)

    Instrumentator().instrument(app).expose(app)

    app.include_router(api_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "path": str(request.url),
                },
            },
        )

    @app.get("/")
    async def root():
        return {
            "name": "AI多Agent教材编写系统",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/docs",
            "health": "/api/monitor/health",
        }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
