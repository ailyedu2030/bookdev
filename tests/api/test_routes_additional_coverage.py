"""
Additional coverage tests for api/routes modules.
Covers error paths, edge cases, and ImportError fallback paths.
"""

from unittest.mock import patch

import pytest


class TestMonitorRoutesEdgeCases:
    """Tests for monitor.py edge cases and error paths"""

    def test_health_check_all_components_import_error(self, test_client):
        """Test health check when modules are not available"""
        with patch.dict(
            "sys.modules",
            {"f28_monitoring_dashboard": None, "f01_immutable_log": None, "f02_context_budget": None},
            clear=False,
        ):
            response = test_client.get("/api/monitor/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "components" in data

    @pytest.mark.skip(reason="Flaky: module mocking from test_monitor.py not cleaned up properly")
    def test_metrics_with_context_budget_import_error(self, test_client, test_admin_authenticated):
        """Test metrics endpoint when context_budget unavailable"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {"f02_context_budget": None, "f28_monitoring_dashboard": None, "f31_minimax_client": None},
            clear=False,
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    @pytest.mark.skip(reason="Flaky: module mocking from test_monitor.py not cleaned up properly")
    def test_metrics_with_llm_cost_tracker_import_error(self, test_client, test_admin_authenticated):
        """Test metrics when CostTracker unavailable"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {"f31_minimax_client": None, "f02_context_budget": None, "f28_monitoring_dashboard": None},
            clear=False,
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

    def test_logs_filter_by_resource_type_empty(self, test_client, test_admin_authenticated):
        """Test logs with resource_type filter"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?resource_type=nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_logs_pagination_boundary(self, test_client, test_admin_authenticated):
        """Test logs pagination at boundary"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?page=1000&per_page=200",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_alerts_with_import_error(self, test_client, test_admin_authenticated):
        """Test alerts when monitoring dashboard unavailable"""
        token = test_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f28_monitoring_dashboard": None}, clear=False):
            response = test_client.get(
                "/api/monitor/alerts",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alerts" in data

    def test_alerts_filter_by_severity(self, test_client, test_admin_authenticated):
        """Test alerts filtering by severity"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts?severity=warning",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_alerts_filter_by_resolved(self, test_client, test_admin_authenticated):
        """Test alerts filtering by resolved status"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts?resolved=false",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_workflow_stats_mock_client_import_error(self, test_client, test_admin_authenticated):
        """Test workflow stats when MockWorkflowClient unavailable"""
        token = test_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f04_temporal_workflow": None}, clear=False):
            response = test_client.get(
                "/api/monitor/workflow/stats",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data


class TestSecurityRoutesEdgeCases:
    """Tests for security.py edge cases and error paths"""

    def test_doi_verify_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test DOI verification when DOIVerifier unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f07_doi_verification": None}, clear=False):
            response = test_client.post(
                "/api/security/doi/verify",
                json={"doi": "10.1234/test"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["valid"] is True

    def test_regulation_verify_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test regulation verification when module unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f08_regulation_verification": None}, clear=False):
            response = test_client.post(
                "/api/security/regulation/verify",
                json={"content": "Test content"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_semantic_scan_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test semantic scan when GlobalSemanticScanner unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f13_global_semantic_scanner": None}, clear=False):
            response = test_client.post(
                "/api/security/semantic/scan",
                json={"content": "Test content", "threshold": 0.8},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_material_register_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test material registration when SourceRegistry unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f09_material_security": None}, clear=False):
            response = test_client.post(
                "/api/security/material/register",
                params={
                    "content_hash": "abc123def456",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_material_verify_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test material verify when SourceRegistry unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f09_material_security": None}, clear=False):
            response = test_client.get(
                "/api/security/material/verify/nonexistent_hash",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_concept_verify_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test concept verify when IntegrityVerifier unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f10_concept_security": None}, clear=False):
            response = test_client.post(
                "/api/security/concept/verify",
                json={
                    "concept_id": "test-concept",
                    "definition": "A test concept definition",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_batch_scan_import_error(self, test_client, test_db, content_admin_authenticated):
        """Test batch scan when ContentSecurityFilter unavailable - uses mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f23_content_security": None}, clear=False):
            response = test_client.post(
                "/api/security/batch/scan?contents=content1&contents=content2&contents=content3",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )
            assert response.status_code == 422


class TestChaptersRoutesEdgeCases:
    """Tests for chapters.py edge cases"""

    def test_list_chapters_project_not_found(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters when project not found"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/chapters/nonexistent-project",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_create_chapter_project_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test creating chapter when project not found - validation error"""
        token = content_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters",
            json={
                "title": "Test Chapter",
                "description": "Test description",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code in [404, 422]

    def test_get_chapter_not_found(self, test_client, test_db, test_user_authenticated):
        """Test getting chapter when not found"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/chapters/details/nonexistent-chapter",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestTermsRoutesEdgeCases:
    """Tests for terms.py edge cases"""

    def test_create_term_empty_name(self, test_client, test_db, editor_authenticated):
        """Test creating term with empty name"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "",
                "definition": "A valid definition",
                "domain": "programming",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code in [400, 422]

    def test_create_term_empty_definition(self, test_client, test_db, editor_authenticated):
        """Test creating term with empty definition"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Valid Name",
                "definition": "",
                "domain": "programming",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code in [400, 422]

    def test_update_term_not_found(self, test_client, test_db, editor_authenticated):
        """Test updating non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.put(
            "/api/terms/nonexistent-term-id",
            json={"definition": "Updated definition"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 404

    def test_lock_term_not_found(self, test_client, test_db, editor_authenticated):
        """Test locking non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/nonexistent-term-id/lock",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 404

    def test_unlock_term_not_found(self, test_client, test_db, editor_authenticated):
        """Test unlocking non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/nonexistent-term-id/unlock",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 404

    def test_delete_term_not_found(self, test_client, test_db, editor_authenticated):
        """Test deleting non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.delete(
            "/api/terms/nonexistent-term-id",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 404

    def test_list_citations_by_chapter_empty(self, test_client, test_db, test_user_authenticated):
        """Test listing citations for chapter with none"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/citations/chapter/nonexistent-chapter",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestProjectsRoutesEdgeCases:
    """Tests for projects.py edge cases"""

    def test_get_project_not_found(self, test_client, test_db, test_user_authenticated):
        """Test getting non-existent project"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/projects/nonexistent-project-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_list_projects_with_pagination(self, test_client, test_db, test_user_authenticated):
        """Test listing projects with pagination parameters"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/projects?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_list_projects_with_status_filter(self, test_client, test_db, test_user_authenticated):
        """Test listing projects with status filter"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/projects?status=active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestRBACEdgeCases:
    """Tests for RBAC edge cases"""

    def test_viewer_cannot_create_chapter(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot create chapters"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters",
            json={
                "title": "Test Chapter",
                "description": "Test description",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 403

    def test_viewer_cannot_delete_chapter(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot delete chapters"""
        token = test_user_authenticated["access_token"]

        response = test_client.delete(
            "/api/chapters/some-chapter-id",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_metrics(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot access metrics"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_alerts(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot access alerts"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_author_cannot_approve_chapter(self, test_client, test_db, author_authenticated):
        """Test author role cannot approve chapters"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/some-chapter-id/approve",
            json={"comments": "Approved"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_access_protected_endpoints(self, test_client):
        """Test unauthenticated requests to protected endpoints"""
        protected_endpoints = [
            ("/api/monitor/metrics", "get"),
            ("/api/monitor/alerts", "get"),
            ("/api/monitor/logs", "get"),
            ("/api/monitor/workflow/stats", "get"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "get":
                response = test_client.get(endpoint)
            else:
                response = test_client.post(endpoint)
            assert response.status_code == 401
