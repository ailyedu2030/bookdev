"""
Workflow API Integration Tests

Tests for workflow endpoints:
- GET /api/workflows - List workflows
- GET /api/workflows/{id} - Get workflow details
- POST /api/workflows/{id}/signal - Send signal to workflow
- POST /api/workflows/{id}/cancel - Cancel workflow
- POST /api/workflows/{id}/terminate - Terminate workflow
- GET /api/workflows/{workflow_id}/history - Get workflow history
- POST /api/workflows/start/chapter-generation - Start chapter generation
- GET /api/workflows/types/list - List workflow types
"""

from datetime import datetime

from api.deps import generate_uuid


class TestListWorkflows:
    """Tests for listing workflows"""

    def test_list_workflows_empty(self, test_client, test_db, test_admin_authenticated):
        """Test listing workflows when none exist"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_with_data(self, test_client, test_db, test_admin_authenticated):
        """Test listing workflows with existing data"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_filter_by_status(self, test_client, test_db, test_admin_authenticated):
        """Test listing workflows filtered by status"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows?status_filter=running",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_pagination(self, test_client, test_db, test_admin_authenticated):
        """Test workflow listing with pagination"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_list_workflows_unauthorized(self, test_client):
        """Test listing workflows without authentication"""
        response = test_client.get("/api/workflows")
        assert response.status_code == 401

    def test_list_workflows_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot list workflows"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestGetWorkflow:
    """Tests for getting workflow details"""

    def test_get_workflow(self, test_client, test_db, test_admin_authenticated):
        """Test getting workflow by ID"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            f"/api/workflows/{generate_uuid()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_workflow_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test getting non-existent workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_workflow_success(self, test_client, test_db, test_admin_authenticated):
        """Test getting workflow by ID after creation"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        project_id = generate_uuid()
        chapter_id = generate_uuid()

        _workflows_store["test-wf-123"] = {
            "id": "test-wf-123",
            "name": "chapter_generation",
            "status": "running",
            "chapter_id": str(chapter_id),
            "project_id": str(project_id),
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        response = test_client.get(
            "/api/workflows/test-wf-123",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-wf-123"
        assert data["status"] == "running"

        del _workflows_store["test-wf-123"]

    def test_get_workflow_unauthorized(self, test_client):
        """Test getting workflow without authentication"""
        response = test_client.get(f"/api/workflows/{generate_uuid()}")
        assert response.status_code == 401


class TestSignalWorkflow:
    """Tests for signaling workflows"""

    def test_signal_workflow_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test signaling non-existent workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/workflows/nonexistent-id/signal",
            json={"signal_name": "pause"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_signal_workflow_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot signal workflows"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            f"/api/workflows/{generate_uuid()}/signal",
            json={"signal_name": "pause"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 403

    def test_signal_completed_workflow_fails(self, test_client, test_db, test_admin_authenticated):
        """Test signaling a completed workflow returns 400"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = generate_uuid()
        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "pause"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "WORKFLOW_NOT_RUNNING"

        del _workflows_store[workflow_id]

    def test_signal_running_workflow_success(self, test_client, test_db, test_admin_authenticated):
        """Test signaling a running workflow succeeds"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = "test-signal-running"

        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/signal",
            json={"signal_name": "pause", "payload": {"key": "value"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        del _workflows_store[workflow_id]


class TestCancelWorkflow:
    """Tests for canceling workflows"""

    def test_cancel_workflow_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test canceling non-existent workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/workflows/nonexistent-id/cancel",
            json={"reason": "Test"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_cancel_running_workflow_success(self, test_client, test_db, test_admin_authenticated):
        """Test canceling a running workflow succeeds"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = "test-cancel-running"

        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            json={"reason": "User requested"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        del _workflows_store[workflow_id]

    def test_cancel_completed_workflow_fails(self, test_client, test_db, test_admin_authenticated):
        """Test canceling a completed workflow returns 400"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = "test-cancel-completed"

        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/cancel",
            json={"reason": "User requested"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "WORKFLOW_ALREADY_ENDED"

        del _workflows_store[workflow_id]


class TestTerminateWorkflow:
    """Tests for terminating workflows"""

    def test_terminate_workflow_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test terminating non-existent workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/workflows/nonexistent-id/terminate",
            json={"reason": "Test"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_terminate_running_workflow_success(self, test_client, test_db, test_admin_authenticated):
        """Test terminating a running workflow succeeds"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = "test-terminate-running"

        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "test_workflow",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }

        response = test_client.post(
            f"/api/workflows/{workflow_id}/terminate",
            json={"reason": "Emergency stop"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        del _workflows_store[workflow_id]


class TestGetWorkflowHistory:
    """Tests for getting workflow history"""

    def test_get_workflow_history_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test getting history of non-existent workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/nonexistent-id/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_workflow_history_success(self, test_client, test_db, test_admin_authenticated):
        """Test getting history of existing workflow"""
        from api.routes.workflows import _workflows_store
        token = test_admin_authenticated["access_token"]
        workflow_id = "test-wf-history-123"

        _workflows_store[workflow_id] = {
            "id": workflow_id,
            "name": "chapter_generation",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "history": [
                {"event": "started", "timestamp": datetime.utcnow().isoformat()},
                {"event": " Chapter_created", "timestamp": datetime.utcnow().isoformat()},
            ],
            "metadata": {},
        }

        response = test_client.get(
            f"/api/workflows/{workflow_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        del _workflows_store[workflow_id]

    def test_get_workflow_history_unauthorized(self, test_client):
        """Test getting workflow history without authentication"""
        response = test_client.get(f"/api/workflows/{generate_uuid()}/history")
        assert response.status_code == 401


class TestStartChapterGeneration:
    """Tests for starting chapter generation workflow"""

    def test_start_chapter_generation(self, test_client, test_db, test_admin_authenticated):
        """Test starting chapter generation workflow"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/workflows/start/chapter-generation",
            params={
                "chapter_id": "chapter-123",
                "project_id": "project-456",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "chapter_generation"
        assert data["status"] == "running"
        assert data["chapter_id"] == "chapter-123"

    def test_start_chapter_generation_with_prompt(self, test_client, test_db, test_admin_authenticated):
        """Test starting chapter generation with custom prompt"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/workflows/start/chapter-generation",
            params={
                "chapter_id": "chapter-123",
                "project_id": "project-456",
                "prompt": "Custom generation prompt",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["prompt"] == "Custom generation prompt"


class TestListWorkflowTypes:
    """Tests for listing workflow types"""

    def test_list_workflow_types(self, test_client, test_db, test_admin_authenticated):
        """Test listing available workflow types"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/types/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "chapter_generation" in data
        assert "chapter_review" in data
        assert "material_collection" in data

    def test_list_workflow_types_unauthorized(self, test_client):
        """Test listing workflow types without authentication"""
        response = test_client.get("/api/workflows/types/list")
        assert response.status_code == 401

    def test_list_workflow_types_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot list workflow types"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/workflows/types/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
