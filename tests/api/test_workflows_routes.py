"""
Additional Workflows API Tests for Higher Coverage

Tests additional endpoints and edge cases for workflow routes.
"""


from api.deps import generate_uuid


class TestWorkflowsAdditional:
    """Additional tests for workflow endpoints"""

    def test_list_workflows_empty(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing workflows when none exist"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_workflows_pagination(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing workflows with pagination"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_filter_by_status(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing workflows filtered by status"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows?status_filter=completed",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_workflow_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting non-existent workflow"""
        token = editor_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/workflows/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_signal_workflow_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling non-existent workflow"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.post(
            f"/api/workflows/{fake_id}/signal",
            json={"signal_name": "test_signal"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_signal_workflow_wrong_status(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling workflow in wrong status"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.post(
            f"/api/workflows/{fake_id}/signal",
            json={"signal_name": "test_signal"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_cancel_workflow_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling non-existent workflow"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.post(
            f"/api/workflows/{fake_id}/cancel",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_terminate_workflow_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test terminating non-existent workflow"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.post(
            f"/api/workflows/{fake_id}/terminate",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_get_workflow_history_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting history of non-existent workflow"""
        token = editor_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/workflows/{fake_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestWorkflowSignals:
    """Tests for workflow signal endpoint - uses correct import path"""

    def test_signal_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully sending a signal to a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-success-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={
                "signal_name": "pause",
                "payload": {"reason": "testing"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["signal"] == "pause"
        assert len(_workflows_store[workflow_id]["signals"]) == 1

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_pending_status(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_workflow",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "resume"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_completed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling a completed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-completed-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "completed_workflow",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "resume"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "WORKFLOW_NOT_RUNNING" in str(data)

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_with_payload(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling with complex payload"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-payload-101"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "payload_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={
                "signal_name": "update_config",
                "payload": {"key": "value", "nested": {"data": 123}},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        signal_entry = _workflows_store[workflow_id]["signals"][0]
        assert signal_entry["signal_name"] == "update_config"
        assert signal_entry["payload"] == {"key": "value", "nested": {"data": 123}}

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowCancel:
    """Tests for workflow cancellation - uses correct import path"""

    def test_cancel_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully cancelling a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-me-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "cancelable_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            params={"reason": "No longer needed"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert _workflows_store[workflow_id]["status"] == "cancelled"
        assert _workflows_store[workflow_id]["cancellation_reason"] == "No longer needed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_pending(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_cancel",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            params={"reason": "Cancelled before start"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        assert _workflows_store[workflow_id]["status"] == "cancelled"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_completed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling an already completed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-completed-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "already_completed",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        assert "WORKFLOW_ALREADY_ENDED" in str(response.json())

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_failed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling a failed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-failed-101"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "failed_workflow",
            "status": "failed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowTerminate:
    """Tests for workflow termination - uses correct import path"""

    def test_terminate_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully terminating a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-me-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "terminatable_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            params={"reason": "Force stop"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert _workflows_store[workflow_id]["status"] == "failed"
        assert _workflows_store[workflow_id]["termination_reason"] == "Force stop"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_terminate_workflow_pending(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test terminating a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_terminate",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            params={"reason": "Emergency stop"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        assert _workflows_store[workflow_id]["status"] == "failed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_terminate_workflow_cancelled_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test terminating an already cancelled workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-cancelled-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "cancelled_workflow",
            "status": "cancelled",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        assert "WORKFLOW_ALREADY_ENDED" in str(response.json())

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowHistory:
    """Tests for workflow history - uses correct import path"""

    def test_get_workflow_history_with_events(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting workflow history with events"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-workflow-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "history_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "history": [
                {
                    "event": "workflow_started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"initiated_by": "user"},
                },
                {
                    "event": "task_completed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"task": "example"},
                },
            ],
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["event"] == "workflow_started"
        assert data[1]["event"] == "task_completed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_get_workflow_history_empty(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting workflow history when no events"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-empty-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "empty_history",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_get_workflow_history_missing_history_key(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting history when history key is missing"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-missing-key-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "no_history_key",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestStartWorkflow:
    """Tests for starting workflows"""

    def test_start_chapter_generation_workflow(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test starting a chapter generation workflow"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        from tests.api.conftest import create_test_chapter, create_test_project
        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/workflows/start/chapter-generation?chapter_id={chapter['id']}&project_id={project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "chapter_generation"
        assert data["status"] == "running"
        assert data["chapter_id"] == chapter["id"]


class TestListWorkflowTypes:
    """Tests for listing workflow types"""

    def test_list_workflow_types(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing available workflow types"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/types/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "chapter_generation" in data
        assert "chapter_review" in data
        assert "material_collection" in data


class TestWorkflowEdgeCases:
    """Edge case tests for workflows"""

    def test_list_workflows_unauthorized(self, test_client):
        """Test listing workflows without authentication"""
        response = test_client.get("/api/workflows")

        assert response.status_code == 401

    def test_get_workflow_unauthorized(self, test_client):
        """Test getting workflow without authentication"""
        response = test_client.get("/api/workflows/some-id")

        assert response.status_code == 401

    def test_signal_workflow_unauthorized(self, test_client):
        """Test signaling workflow without authentication"""
        response = test_client.post(
            "/api/workflows/some-id/signal",
            json={"signal_name": "test"},
        )

        assert response.status_code == 401

    def test_cancel_workflow_unauthorized(self, test_client):
        """Test cancelling workflow without authentication"""
        response = test_client.post("/api/workflows/some-id/cancel")

        assert response.status_code == 401

    def test_terminate_workflow_unauthorized(self, test_client):
        """Test terminating workflow without authentication"""
        response = test_client.post("/api/workflows/some-id/terminate")

        assert response.status_code == 401

    def test_get_history_unauthorized(self, test_client):
        """Test getting workflow history without authentication"""
        response = test_client.get("/api/workflows/some-id/history")

        assert response.status_code == 401

    def test_start_workflow_unauthorized(self, test_client):
        """Test starting workflow without authentication"""
        response = test_client.post(
            "/api/workflows/start/chapter-generation?chapter_id=abc&project_id=xyz",
        )

        assert response.status_code == 401

    def test_list_workflow_types_unauthorized(self, test_client):
        """Test listing workflow types without authentication"""
        response = test_client.get("/api/workflows/types/list")

        assert response.status_code == 401


class TestWorkflowSignalsFixed:
    """Tests for workflow signal endpoint - uses correct import path"""

    def test_signal_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully sending a signal to a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-success-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={
                "signal_name": "pause",
                "payload": {"reason": "testing"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["signal"] == "pause"
        assert len(_workflows_store[workflow_id]["signals"]) == 1

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_pending_status(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_workflow",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "resume"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_completed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling a completed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-completed-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "completed_workflow",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "resume"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "WORKFLOW_NOT_RUNNING" in str(data)

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_signal_workflow_with_payload(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test signaling with complex payload"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "sig-payload-101"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "payload_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "signals": [],
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={
                "signal_name": "update_config",
                "payload": {"key": "value", "nested": {"data": 123}},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        signal_entry = _workflows_store[workflow_id]["signals"][0]
        assert signal_entry["signal_name"] == "update_config"
        assert signal_entry["payload"] == {"key": "value", "nested": {"data": 123}}

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowCancelFixed:
    """Tests for workflow cancellation - uses correct import path"""

    def test_cancel_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully cancelling a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-me-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "cancelable_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            params={"reason": "No longer needed"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert _workflows_store[workflow_id]["status"] == "cancelled"
        assert _workflows_store[workflow_id]["cancellation_reason"] == "No longer needed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_pending(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_cancel",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            params={"reason": "Cancelled before start"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        assert _workflows_store[workflow_id]["status"] == "cancelled"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_completed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling an already completed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-completed-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "already_completed",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        assert "WORKFLOW_ALREADY_ENDED" in str(response.json())

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_cancel_workflow_failed_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test cancelling a failed workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "cancel-failed-101"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "failed_workflow",
            "status": "failed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowTerminateFixed:
    """Tests for workflow termination - uses correct import path"""

    def test_terminate_workflow_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully terminating a running workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-me-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "terminatable_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            params={"reason": "Force stop"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert _workflows_store[workflow_id]["status"] == "failed"
        assert _workflows_store[workflow_id]["termination_reason"] == "Force stop"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_terminate_workflow_pending(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test terminating a pending workflow"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-pending-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "pending_terminate",
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            params={"reason": "Emergency stop"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        assert _workflows_store[workflow_id]["status"] == "failed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_terminate_workflow_cancelled_fails(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test terminating an already cancelled workflow returns 400"""
        token = content_admin_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "terminate-cancelled-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "cancelled_workflow",
            "status": "cancelled",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        assert "WORKFLOW_ALREADY_ENDED" in str(response.json())

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestWorkflowHistoryFixed:
    """Tests for workflow history - uses correct import path"""

    def test_get_workflow_history_with_events(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting workflow history with events"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-workflow-123"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "history_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "history": [
                {
                    "event": "workflow_started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"initiated_by": "user"},
                },
                {
                    "event": "task_completed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"task": "example"},
                },
            ],
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["event"] == "workflow_started"
        assert data[1]["event"] == "task_completed"

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_get_workflow_history_empty(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting workflow history when no events"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-empty-456"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "empty_history",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]

    def test_get_workflow_history_missing_history_key(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting history when history key is missing"""
        token = editor_authenticated["access_token"]

        from datetime import datetime

        from api.routes.workflows import _workflows_store

        workflow_id = "history-missing-key-789"
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "no_history_key",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]


class TestStartWorkflowFixed:
    """Tests for starting workflows - uses correct import path"""

    def test_start_chapter_generation_workflow(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test starting a chapter generation workflow"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        from tests.api.conftest import create_test_chapter, create_test_project
        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/workflows/start/chapter-generation?chapter_id={chapter['id']}&project_id={project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "chapter_generation"
        assert data["status"] == "running"
        assert data["chapter_id"] == chapter["id"]
        assert "id" in data

    def test_start_chapter_generation_with_prompt(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test starting workflow with custom prompt"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        from tests.api.conftest import create_test_chapter, create_test_project
        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/workflows/start/chapter-generation?chapter_id={chapter['id']}&project_id={project['id']}&prompt=Custom%20prompt",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "chapter_generation"
        assert data["metadata"]["prompt"] == "Custom prompt"


class TestListWorkflowTypesFixed:
    """Tests for listing workflow types"""

    def test_list_workflow_types(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing available workflow types"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/types/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "chapter_generation" in data
        assert "chapter_review" in data
        assert "material_collection" in data
        assert "semantic_scan" in data
        assert "full_pipeline" in data
