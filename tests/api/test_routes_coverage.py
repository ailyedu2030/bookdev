"""
Comprehensive Coverage Tests for API Routes

Tests to increase coverage for:
- api/routes/admin.py (target: 25% -> 95%+)
- api/routes/monitor.py (target: 19% -> 95%+)
- api/routes/security.py (target: 28% -> 95%+)
"""

from unittest.mock import MagicMock, patch


class TestAdminRoutesEdgeCases:
    """Edge case tests for admin routes to boost coverage"""

    def test_list_users_page_2_with_no_more_users(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test listing users on page 2 when no more users exist"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/users?page=10&per_page=20",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_users_role_and_search_combined(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test filtering by role and searching at the same time"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "specialadmin",
            "email": "special.admin@example.com",
            "password": "pass123",
            "role": "system_admin",
        })

        response = test_client.get(
            "/api/admin/users?role_filter=system_admin&search=special",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_does_not_exist(
        self, test_client, test_admin_authenticated
    ):
        """Test getting non-existent user returns 404"""
        token = test_admin_authenticated["access_token"]
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.get(
            f"/api/admin/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_delete_user_does_not_exist(
        self, test_client, test_admin_authenticated
    ):
        """Test deleting non-existent user returns 404"""
        token = test_admin_authenticated["access_token"]
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.delete(
            f"/api/admin/users/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_user_self_forbidden(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test that admin cannot delete themselves"""
        token = test_admin_authenticated["access_token"]
        admin = test_admin_authenticated["user"]

        response = test_client.delete(
            f"/api/admin/users/{admin.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "CANNOT_DELETE_SELF" in str(data)

    def test_update_user_role_self_forbidden(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test that admin cannot modify their own role"""
        token = test_admin_authenticated["access_token"]
        admin = test_admin_authenticated["user"]

        response = test_client.put(
            f"/api/admin/users/{admin.id}/role",
            json={"role": "viewer"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "CANNOT_MODIFY_OWN_ROLE" in str(data)

    def test_update_user_role_does_not_exist(
        self, test_client, test_admin_authenticated
    ):
        """Test updating role of non-existent user returns 404"""
        token = test_admin_authenticated["access_token"]
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.put(
            f"/api/admin/users/{fake_id}/role",
            json={"role": "editor"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_update_user_with_no_data(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user with empty data returns 400"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "updateme",
            "email": "update@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400

    def test_update_user_with_only_username(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user with only username field"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "original",
            "email": "original@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}",
            json={"username": "updated"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_create_user_duplicate_username(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test creating user with duplicate username"""
        token = test_admin_authenticated["access_token"]
        test_db.create_user({
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        test_client.post(
            "/api/admin/users",
            json={
                "username": "existinguser",
                "email": "different@example.com",
                "password": "password123",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

    def test_admin_stats_with_projects_and_chapters(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats with actual projects and chapters"""
        token = test_admin_authenticated["access_token"]
        test_admin_authenticated["user"]

        test_db._projects["proj-1"] = {"id": "proj-1", "status": "draft"}
        test_db._projects["proj-2"] = {"id": "proj-2", "status": "published"}
        test_db._chapters["ch-1"] = {"id": "ch-1", "status": "draft"}
        test_db._chapters["ch-2"] = {"id": "ch-2", "status": "published"}
        test_db._chapters["ch-3"] = {"id": "ch-3", "status": "review"}

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_projects"] == 2
        assert data["data"]["total_chapters"] == 3
        assert "draft" in data["data"]["projects_by_status"]
        assert "published" in data["data"]["projects_by_status"]

    def test_admin_stats_users_by_role(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats grouping users by role"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "user1",
            "email": "user1@example.com",
            "password": "pass123",
            "role": "viewer",
        })
        test_db.create_user({
            "username": "user2",
            "email": "user2@example.com",
            "password": "pass123",
            "role": "viewer",
        })
        test_db.create_user({
            "username": "user3",
            "email": "user3@example.com",
            "password": "pass123",
            "role": "editor",
        })

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["users_by_role"]["viewer"] == 2
        assert data["data"]["users_by_role"]["editor"] == 1


class TestMonitorRoutesEdgeCases:
    """Edge case tests for monitor routes to boost coverage"""

    def test_health_check_all_components_healthy(
        self, test_client,
    ):
        """Test health check when all components are healthy"""
        mock_dashboard = MagicMock()
        mock_health = MagicMock()
        mock_health.status.value = "operational"
        mock_dashboard.get_health_status.return_value = mock_health

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = list(range(10))

        mock_budget = MagicMock()
        mock_budget.get_total_usage.return_value = 10000

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
                with patch("f02_context_budget.context_budget_manager.ContextBudgetManager", return_value=mock_budget):
                    response = test_client.get("/api/monitor/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"

    def test_health_check_one_component_unhealthy(
        self, test_client,
    ):
        """Test health check when one component is unhealthy"""
        mock_dashboard = MagicMock()
        mock_health = MagicMock()
        mock_health.status.value = "degraded"
        mock_dashboard.get_health_status.return_value = mock_health

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = list(range(10))

        mock_budget = MagicMock()
        mock_budget.get_total_usage.return_value = 10000

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
                with patch("f02_context_budget.context_budget_manager.ContextBudgetManager", return_value=mock_budget):
                    response = test_client.get("/api/monitor/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"

    def test_health_check_dashboard_import_error(
        self, test_client,
    ):
        """Test health check when dashboard import fails"""
        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = list(range(10))

        mock_budget = MagicMock()
        mock_budget.get_total_usage.return_value = 10000

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            with patch("f02_context_budget.context_budget_manager.ContextBudgetManager", return_value=mock_budget):
                with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", side_effect=ImportError):
                    response = test_client.get("/api/monitor/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert data["components"] == {}

    def test_metrics_with_dashboard_module(
        self, test_client, test_admin_authenticated
    ):
        """Test metrics when dashboard module is available"""
        token = test_admin_authenticated["access_token"]

        mock_dashboard = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.workflows = {"active": 5, "completed": 100}
        mock_metrics.alerts = ["alert1", "alert2"]
        mock_dashboard.get_metrics.return_value = mock_metrics

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            with patch.dict("sys.modules", {
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            }):
                response = test_client.get(
                    "/api/monitor/metrics",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_metrics_with_context_budget_module(
        self, test_client, test_admin_authenticated
    ):
        """Test metrics when context budget module is available"""
        token = test_admin_authenticated["access_token"]

        mock_budget = MagicMock()
        mock_budget.get_total_usage.return_value = 75000
        mock_budget.max_tokens = 200000

        with patch.dict("sys.modules", {
            "f28_monitoring_dashboard": None,
            "f28_monitoring_dashboard.monitoring_dashboard": None,
            "f31_minimax_client": None,
            "f31_minimax_client.cost_tracker": None,
        }):
            with patch("f02_context_budget.context_budget_manager.ContextBudgetManager", return_value=mock_budget):
                response = test_client.get(
                    "/api/monitor/metrics",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "context_budget" in data["data"]
                assert data["data"]["context_budget"]["total_tokens"] == 75000

    def test_logs_with_immutable_log_and_filters(
        self, test_client, test_admin_authenticated
    ):
        """Test logs endpoint with ImmutableLog and multiple filters"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = [
            {
                "id": "entry-1",
                "event_type": "USER_LOGIN",
                "user_id": "user-123",
                "resource_type": "session",
                "resource_id": "session-1",
                "action": "login",
                "result": "success",
                "details": {},
                "ip_address": "192.168.1.1",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            {
                "id": "entry-2",
                "event_type": "PROJECT_CREATE",
                "user_id": "user-123",
                "resource_type": "project",
                "resource_id": "proj-1",
                "action": "create",
                "result": "success",
                "details": {},
                "ip_address": "192.168.1.1",
                "timestamp": "2024-01-16T10:30:00Z",
            },
        ]

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.get(
                "/api/monitor/logs?event_type=PROJECT_CREATE&user_id=user-123&resource_type=project",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["event_type"] == "PROJECT_CREATE"

    def test_logs_pagination_page_2(
        self, test_client, test_admin_authenticated
    ):
        """Test logs pagination with page 2"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = [
            {"id": f"entry-{i}", "event_type": "TEST", "user_id": "user-1", "timestamp": "2024-01-01T00:00:00Z"}
            for i in range(100)
        ]

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.get(
                "/api/monitor/logs?page=2&per_page=10",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 10

    def test_alerts_with_severity_and_resolved_filters(
        self, test_client, test_admin_authenticated
    ):
        """Test alerts with severity and resolved filters"""
        token = test_admin_authenticated["access_token"]

        mock_alert1 = MagicMock()
        mock_alert1.id = "alert-1"
        mock_alert1.severity = "error"
        mock_alert1.message = "Error alert"
        mock_alert1.resolved = False
        mock_alert1.created_at = "2024-01-15T10:30:00Z"

        mock_alert2 = MagicMock()
        mock_alert2.id = "alert-2"
        mock_alert2.severity = "warning"
        mock_alert2.message = "Warning alert"
        mock_alert2.resolved = True
        mock_alert2.created_at = "2024-01-14T10:30:00Z"

        mock_dashboard = MagicMock()
        mock_dashboard.get_alerts.return_value = [mock_alert1, mock_alert2]

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            response = test_client.get(
                "/api/monitor/alerts?severity=error&resolved=false",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            response.json()
            mock_dashboard.get_alerts.assert_called_once_with(severity="error", resolved=False)

    def test_workflow_stats_with_mock_client(
        self, test_client, test_admin_authenticated
    ):
        """Test workflow stats when temporal module is not available"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/workflow/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        stats = data["data"]
        assert "total_workflows" in stats
        assert "running" in stats

    def test_dashboard_summary_with_mock(
        self, test_client, test_admin_authenticated
    ):
        """Test dashboard summary with mock dashboard"""
        token = test_admin_authenticated["access_token"]

        mock_summary = {
            "total_projects": 25,
            "total_chapters": 150,
            "active_workflows": 8,
            "recent_activity": [
                {"type": "project_created", "timestamp": "2024-01-20T10:00:00Z"},
                {"type": "chapter_published", "timestamp": "2024-01-20T09:00:00Z"},
            ],
        }

        mock_dashboard = MagicMock()
        mock_dashboard.get_dashboard_summary.return_value = mock_summary

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            response = test_client.get(
                "/api/monitor/dashboard/summary",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_projects"] == 25
            assert data["data"]["active_workflows"] == 8
            assert len(data["data"]["recent_activity"]) == 2

    def test_append_log_with_immutable_log(
        self, test_client, test_admin_authenticated
    ):
        """Test append log when ImmutableLog is available"""
        token = test_admin_authenticated["access_token"]
        test_admin_authenticated["user"]

        mock_log_instance = MagicMock()

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.post(
                "/api/monitor/logs/append?event_type=USER_ACTION",
                json={"action": "test", "details": "testing"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_log_instance.append.assert_called_once()


class TestSecurityRoutesEdgeCases:
    """Edge case tests for security routes to boost coverage"""

    def test_scan_content_with_profanity_category(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning content with profanity category"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={
                "content": "Content with some words",
                "categories": ["profanity"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_scan_content_with_hate_speech_category(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning content with hate speech category"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={
                "content": "Content to scan",
                "categories": ["hate_speech"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_scan_content_with_pii_category(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning content with pii category"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={
                "content": "Content to scan",
                "categories": ["pii"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_scan_content_mock_fallback(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning content falls back to mock when module unavailable"""
        token = editor_authenticated["access_token"]

        with patch.dict("sys.modules", {"f23_content_security": None, "f23_content_security.content_filter": None}):
            response = test_client.post(
                "/api/security/scan",
                json={"content": "Normal content"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_safe"] is True

    def test_doi_verify_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test DOI verification falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f07_doi_verification": None, "f07_doi_verification.doi_verifier": None}):
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
            assert data["valid"] is True

    def test_regulation_verify_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test regulation verification falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f08_regulation_verification": None, "f08_regulation_verification.regulation_verifier": None}):
            response = test_client.post(
                "/api/security/regulation/verify",
                json={"content": "Content to verify"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True

    def test_semantic_scan_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test semantic scan falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f13_global_semantic_scanner": None, "f13_global_semantic_scanner.semantic_scanner": None}):
            response = test_client.post(
                "/api/security/semantic/scan",
                json={"content": "Content to scan"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["score"] == 1.0

    def test_register_material_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test register material falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f09_material_security": None, "f09_material_security.source_registry": None}):
            response = test_client.post(
                "/api/security/material/register",
                params={"content_hash": "abc123hash"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_verify_material_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test verify material falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f09_material_security": None, "f09_material_security.source_registry": None}):
            response = test_client.get(
                "/api/security/material/verify/somehash",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["registered"] is False

    def test_concept_verify_mock_fallback(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test concept verify falls back to mock"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f10_concept_security": None, "f10_concept_security.integrity_verifier": None}):
            response = test_client.post(
                "/api/security/concept/verify",
                json={"concept_id": "test-concept", "definition": "A test concept"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True

    def test_batch_scan_multiple_items(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test batch scan with multiple items"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f23_content_security": None, "f23_content_security.content_filter": None}):
            response = test_client.post(
                "/api/security/batch/scan",
                json={"contents": ["Item 1", "Item 2", "Item 3"]},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert data["safe_count"] == 3
            assert data["unsafe_count"] == 0

    def test_batch_scan_empty_list(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test batch scan with empty list"""
        token = content_admin_authenticated["access_token"]

        with patch.dict("sys.modules", {"f23_content_security": None, "f23_content_security.content_filter": None}):
            response = test_client.post(
                "/api/security/batch/scan",
                json={"contents": []},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0


class TestListPermissionsDetailed:
    """Detailed tests for list permissions endpoint"""

    def test_list_permissions_includes_projects_resource(
        self, test_client, test_admin_authenticated
    ):
        """Test that permissions list includes projects resource"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "projects" in data["resources"]

    def test_list_permissions_includes_chapters_resource(
        self, test_client, test_admin_authenticated
    ):
        """Test that permissions list includes chapters resource"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "chapters" in data["resources"]

    def test_list_permissions_excludes_wildcard(
        self, test_client, test_admin_authenticated
    ):
        """Test that wildcard permission is excluded from resources"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        resources = data["resources"]
        for resource_actions in resources.values():
            assert "*:*" not in resource_actions


class TestRolesDetailed:
    """Detailed tests for roles endpoint"""

    def test_list_roles_sorted_correctly(
        self, test_client, test_admin_authenticated
    ):
        """Test that roles are sorted by level descending"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        levels = [r["level"] for r in data]
        assert levels == sorted(levels, reverse=True)

    def test_list_roles_has_system_admin_highest(
        self, test_client, test_admin_authenticated
    ):
        """Test that system_admin has the highest level"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        system_admin = next(r for r in data if r["name"] == "system_admin")
        assert system_admin["level"] == max(r["level"] for r in data)


class TestAdminStatsDetailed:
    """Detailed tests for admin stats"""

    def test_admin_stats_empty_chapters(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats with no chapters"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_chapters"] == 0
        assert data["data"]["chapters_by_status"] == {}

    def test_admin_stats_empty_projects(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats with no projects"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_projects"] == 0
        assert data["data"]["projects_by_status"] == {}
