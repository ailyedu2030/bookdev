"""
Workflow Routes

Handles Temporal workflow operations:
- GET /api/workflows - List workflows
- GET /api/workflows/{id} - Get workflow details
- POST /api/workflows/{id}/signal - Send signal to workflow
- POST /api/workflows/{id}/cancel - Cancel workflow
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from api.schemas.common import SuccessResponse
from api.deps import get_current_active_user, User, require_permission, generate_uuid
from api.middleware.csrf import csrf_protect

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


_workflows_store: Dict[str, dict] = {}


class WorkflowSignalRequest(BaseModel):
    signal_name: str
    payload: Optional[dict] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    status: str
    chapter_id: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    metadata: dict = {}


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    status_filter: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_permission("workflows:read")),
):
    """
    List all workflows.

    - **status_filter**: Filter by status (pending, running, completed, failed, cancelled)
    - **page**: Page number
    - **per_page**: Items per page
    """
    workflows = list(_workflows_store.values())

    if status_filter:
        workflows = [w for w in workflows if w.get("status") == status_filter]

    total = len(workflows)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return [WorkflowResponse(**w) for w in workflows[start_idx:end_idx]]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    user: User = Depends(require_permission("workflows:read")),
):
    """
    Get workflow details by ID.
    """
    workflow = _workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": "Workflow not found",
                }
            },
        )

    return WorkflowResponse(**workflow)


@router.post(
    "/{workflow_id}/signal",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def signal_workflow(
    workflow_id: str,
    signal_request: WorkflowSignalRequest,
    user: User = Depends(require_permission("workflows:signal")),
):
    """
    Send a signal to a running workflow.

    - **workflow_id**: Workflow ID
    - **signal_name**: Name of the signal
    - **payload**: Signal payload data
    """
    workflow = _workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": "Workflow not found",
                }
            },
        )

    if workflow.get("status") not in ("running", "pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_RUNNING",
                    "message": f"Cannot signal workflow in status: {workflow.get('status')}",
                }
            },
        )

    if "signals" not in workflow:
        workflow["signals"] = []
    workflow["signals"].append({
        "signal_name": signal_request.signal_name,
        "payload": signal_request.payload,
        "timestamp": datetime.utcnow().isoformat(),
        "sent_by": user.id,
    })

    _workflows_store[workflow_id] = workflow

    return SuccessResponse(
        success=True,
        message=f"Signal '{signal_request.signal_name}' sent successfully",
        data={"workflow_id": workflow_id, "signal": signal_request.signal_name},
    )


@router.post(
    "/{workflow_id}/cancel",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def cancel_workflow(
    workflow_id: str,
    reason: Optional[str] = None,
    user: User = Depends(require_permission("workflows:cancel")),
):
    """
    Cancel a running workflow.

    - **workflow_id**: Workflow ID
    - **reason**: Cancellation reason (max 500 characters)
    """
    # API-SEC-013: Validate reason length
    if reason and len(reason) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "REASON_TOO_LONG",
                    "message": "Cancellation reason must be 500 characters or less",
                }
            },
        )
    workflow = _workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": "Workflow not found",
                }
            },
        )

    if workflow.get("status") in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WORKFLOW_ALREADY_ENDED",
                    "message": f"Cannot cancel workflow in status: {workflow.get('status')}",
                }
            },
        )

    workflow["status"] = "cancelled"
    workflow["completed_at"] = datetime.utcnow().isoformat()
    workflow["cancellation_reason"] = reason
    workflow["cancelled_by"] = user.id

    _workflows_store[workflow_id] = workflow

    return SuccessResponse(
        success=True,
        message="Workflow cancelled successfully",
        data={"workflow_id": workflow_id},
    )


@router.post(
    "/{workflow_id}/terminate",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def terminate_workflow(
    workflow_id: str,
    reason: Optional[str] = None,
    user: User = Depends(require_permission("workflows:terminate")),
):
    """
    Forcefully terminate a workflow.

    - **workflow_id**: Workflow ID
    - **reason**: Termination reason (max 500 characters)
    """
    # API-SEC-013: Validate reason length
    if reason and len(reason) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "REASON_TOO_LONG",
                    "message": "Termination reason must be 500 characters or less",
                }
            },
        )
    workflow = _workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": "Workflow not found",
                }
            },
        )

    if workflow.get("status") in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WORKFLOW_ALREADY_ENDED",
                    "message": f"Cannot terminate workflow in status: {workflow.get('status')}",
                }
            },
        )

    workflow["status"] = "failed"
    workflow["completed_at"] = datetime.utcnow().isoformat()
    workflow["termination_reason"] = reason
    workflow["terminated_by"] = user.id

    _workflows_store[workflow_id] = workflow

    return SuccessResponse(
        success=True,
        message="Workflow terminated successfully",
        data={"workflow_id": workflow_id},
    )


@router.get("/{workflow_id}/history", response_model=list)
async def get_workflow_history(
    workflow_id: str,
    user: User = Depends(require_permission("workflows:read")),
):
    """
    Get workflow execution history.
    """
    workflow = _workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": "Workflow not found",
                }
            },
        )

    history = workflow.get("history", [])

    return [
        {
            "event": event.get("event", "unknown"),
            "timestamp": event.get("timestamp"),
            "details": event.get("details", {}),
        }
        for event in history
    ]


@router.post(
    "/start/chapter-generation",
    response_model=WorkflowResponse,
    dependencies=[Depends(csrf_protect)],
)
async def start_chapter_generation_workflow(
    chapter_id: str,
    project_id: str,
    prompt: Optional[str] = None,
    user: User = Depends(require_permission("workflows:create")),
):
    """
    Start a chapter generation workflow.

    - **chapter_id**: Chapter ID to generate
    - **project_id**: Project ID
    - **prompt**: Optional custom prompt
    """
    workflow_id = generate_uuid()
    now = datetime.utcnow().isoformat()

    workflow = {
        "id": workflow_id,
        "name": "chapter_generation",
        "status": "running",
        "chapter_id": chapter_id,
        "project_id": project_id,
        "started_at": now,
        "completed_at": None,
        "metadata": {
            "prompt": prompt,
            "started_by": user.id,
        },
        "history": [
            {
                "event": "workflow_started",
                "timestamp": now,
                "details": {"chapter_id": chapter_id},
            }
        ],
        "signals": [],
    }

    _workflows_store[workflow_id] = workflow

    return WorkflowResponse(**workflow)


@router.get("/types/list", response_model=List[str])
async def list_workflow_types(
    user: User = Depends(require_permission("workflows:read")),
):
    """
    List available workflow types.
    """
    return [
        "chapter_generation",
        "chapter_review",
        "material_collection",
        "semantic_scan",
        "full_pipeline",
    ]
