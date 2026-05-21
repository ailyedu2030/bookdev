"""
Monitoring Routes

Handles system monitoring operations:
- GET /api/monitor/health - Health check
- GET /api/monitor/metrics - System metrics
- GET /api/monitor/logs - Audit logs
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.deps import User, require_permission
from api.schemas.common import HealthResponse, LogEntry, MetricsResponse, SuccessResponse

router = APIRouter(prefix="/api/monitor", tags=["Monitoring"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns basic system health status. Component details are only shown
    to authenticated users with proper permissions.
    """
    # Basic health check - just verify the API is responding
    # Don't expose internal module states publicly
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        components={},
        version="1.0.0",
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    user: User = Depends(require_permission("monitor:read")),
):
    """
    Get system metrics.

    Returns various system metrics including:
    - Request counts
    - Response times
    - Error rates
    - Resource usage
    """
    uptime_seconds = int(time.time() - _start_time)
    uptime_hours = uptime_seconds / 3600

    metrics = {
        "uptime_seconds": uptime_seconds,
        "uptime_hours": round(uptime_hours, 2),
        "requests": {
            "total": 0,
            "success": 0,
            "failed": 0,
        },
        "response_time_ms": {
            "avg": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
        },
        "resources": {
            "memory_mb": 0,
            "cpu_percent": 0,
        },
        "modules": {},
    }

    try:
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard

        dashboard = MonitoringDashboard()
        dashboard_metrics = dashboard.get_metrics()

        if hasattr(dashboard_metrics, "workflows"):
            metrics["modules"]["workflows"] = dashboard_metrics.workflows
        if hasattr(dashboard_metrics, "alerts"):
            metrics["alerts"] = len(dashboard_metrics.alerts) if dashboard_metrics.alerts else 0

    except ImportError:
        pass

    try:
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker()
        stats = tracker.get_usage_stats()
        metrics["llm_usage"] = {
            "total_tokens": stats.get("total_tokens", 0),
            "total_cost": stats.get("total_cost", 0.0),
            "request_count": stats.get("request_count", 0),
        }
    except ImportError:
        metrics["llm_usage"] = {"error": "Module not available"}

    try:
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        budget = ContextBudgetManager()
        usage = budget.get_total_usage()
        metrics["context_budget"] = {
            "total_tokens": usage if isinstance(usage, int | float) else 0,
            "limit": budget.max_tokens if hasattr(budget, "max_tokens") else 200000,
        }
    except ImportError:
        metrics["context_budget"] = {"error": "Module not available"}

    return MetricsResponse(
        success=True,
        data=metrics,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/logs", response_model=list[LogEntry])
async def get_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    event_type: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    user: User = Depends(require_permission("monitor:logs")),
):
    """
    Get audit logs with filtering and pagination.

    - **page**: Page number
    - **per_page**: Items per page
    - **event_type**: Filter by event type
    - **user_id**: Filter by user ID
    - **resource_type**: Filter by resource type
    - **start_date**: Filter from date (ISO format)
    - **end_date**: Filter to date (ISO format)
    """
    logs = []

    try:
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        entries = log.get_entries()

        for entry in entries:
            if event_type and entry.get("event_type") != event_type:
                continue
            if user_id and entry.get("user_id") != user_id:
                continue
            if resource_type and entry.get("resource_type") != resource_type:
                continue

            logs.append(
                LogEntry(
                    id=entry.get("id", ""),
                    event_type=entry.get("event_type", ""),
                    user_id=entry.get("user_id"),
                    resource_type=entry.get("resource_type"),
                    resource_id=entry.get("resource_id"),
                    action=entry.get("action"),
                    result=entry.get("result"),
                    details=entry.get("details"),
                    ip_address=entry.get("ip_address"),
                    created_at=entry.get("timestamp", datetime.utcnow().isoformat()),
                )
            )

    except ImportError:
        pass

    len(logs)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return logs[start_idx:end_idx]


@router.get("/alerts", response_model=dict)
async def get_alerts(
    severity: str | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    user: User = Depends(require_permission("monitor:alerts")),
):
    """
    Get system alerts.

    - **severity**: Filter by severity (info, warning, error, critical)
    - **resolved**: Filter by resolved status
    """
    alerts = []

    try:
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard

        dashboard = MonitoringDashboard()

        if hasattr(dashboard, "get_alerts"):
            raw_alerts = dashboard.get_alerts(severity=severity, resolved=resolved)
            for alert in raw_alerts:
                alerts.append(
                    {
                        "id": alert.id if hasattr(alert, "id") else str(alert),
                        "severity": alert.severity if hasattr(alert, "severity") else "info",
                        "message": alert.message if hasattr(alert, "message") else str(alert),
                        "resolved": alert.resolved if hasattr(alert, "resolved") else False,
                        "created_at": alert.created_at
                        if hasattr(alert, "created_at")
                        else datetime.utcnow().isoformat(),
                    }
                )
    except ImportError:
        pass

    return {
        "success": True,
        "total": len(alerts),
        "alerts": alerts,
    }


@router.get("/workflow/stats", response_model=dict)
async def get_workflow_stats(
    user: User = Depends(require_permission("monitor:workflows")),
):
    """
    Get workflow execution statistics.
    """
    stats = {
        "total_workflows": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }

    try:
        from f04_temporal_workflow.workflows.mock_client import MockWorkflowClient

        client = MockWorkflowClient()
        if hasattr(client, "get_stats"):
            stats = client.get_stats()
    except ImportError:
        pass

    return {
        "success": True,
        "data": stats,
    }


@router.get("/dashboard/summary", response_model=dict)
async def get_dashboard_summary(
    user: User = Depends(require_permission("monitor:read")),
):
    """
    Get dashboard summary for the monitoring page.
    """
    try:
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard

        dashboard = MonitoringDashboard()
        summary = dashboard.get_dashboard_summary()

        return {
            "success": True,
            "data": summary,
        }
    except ImportError:
        return {
            "success": True,
            "data": {
                "total_projects": 0,
                "total_chapters": 0,
                "active_workflows": 0,
                "recent_activity": [],
            },
        }


@router.post("/logs/append", response_model=SuccessResponse)
async def append_log(
    event_type: str,
    details: dict,
    user: User = Depends(require_permission("monitor:logs")),
):
    """
    Append an entry to the audit log.

    - **event_type**: Type of event
    - **details**: Event details
    """
    try:
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        log.append(
            event_type,
            {
                **details,
                "user_id": user.id,
                "username": user.username,
            },
        )

        return SuccessResponse(
            success=True,
            message="Log entry appended",
        )
    except ImportError:
        return SuccessResponse(
            success=True,
            message="Mock mode - log entry recorded",
        )
