"""
RBAC (Role-Based Access Control) Integration Tests

Tests for role-based permission enforcement:
- Viewer: read-only access to projects, chapters, terms
- Author: can create/edit own content
- Editor: can edit chapters, terms, lock terms
- Reviewer: can approve/reject chapters
- Content Admin: manage content, users
- System Admin: full system access
"""


from api.deps import generate_uuid

from tests.api.conftest import (
    create_test_chapter,
    create_test_project,
    create_test_term,
)


class TestViewerPermissions:
    """Tests for viewer role permissions"""

    def test_viewer_can_read_projects(self, test_client, test_db, test_user_authenticated):
        """Test viewer can read projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_viewer_cannot_create_projects(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot create projects"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/projects",
            json={"name": "Unauthorized Project"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_viewer_cannot_update_projects(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot update projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.put(
            f"/api/projects/{project['id']}",
            json={"name": "Updated Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_viewer_cannot_delete_projects(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot delete projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_viewer_can_read_chapters(self, test_client, test_db, test_user_authenticated):
        """Test viewer can read chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.get(
            f"/api/chapters/detail/{chapter['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_viewer_cannot_create_chapters(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot create chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Unauthorized Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_viewer_cannot_update_chapters(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot update chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "Updated Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_viewer_can_read_terms(self, test_client, test_db, test_user_authenticated):
        """Test viewer can read terms"""
        token = test_user_authenticated["access_token"]

        term = create_test_term(test_db, term="Python", definition="Programming lang")

        response = test_client.get(
            f"/api/terms/{term['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_viewer_cannot_create_terms(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot create terms"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Unauthorized Term",
                "definition": "Definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestAuthorPermissions:
    """Tests for author role permissions"""

    def test_author_can_create_own_chapter(self, test_client, test_db, author_authenticated):
        """Test author can create their own chapters"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Author's Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201

    def test_author_can_update_own_chapter(self, test_client, test_db, author_authenticated):
        """Test author can update their own chapters"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], author_id=user.id)

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "Updated by Author"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_author_can_update_others_chapters(self, test_client, test_db, author_authenticated):
        """Test author CAN update other authors' chapters due to RBAC permissions"""
        token = author_authenticated["access_token"]

        other_user_id = generate_uuid()
        project = create_test_project(test_db, owner_id=other_user_id)
        chapter = create_test_chapter(test_db, project_id=project["id"], author_id=other_user_id)

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "Authorized Update"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_author_cannot_approve_chapters(self, test_client, test_db, author_authenticated):
        """Test author cannot approve chapters"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], author_id=user.id, status="reviewing")

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/approve",
            json={"comments": "Approved", "chapter_id": chapter["id"]},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_author_can_search_terms(self, test_client, test_db, author_authenticated):
        """Test author can search terms"""
        token = author_authenticated["access_token"]

        create_test_term(test_db, term="Python", definition="Programming lang")

        response = test_client.post(
            "/api/terms/search",
            json={"query": "Python"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


class TestEditorPermissions:
    """Tests for editor role permissions"""

    def test_editor_can_create_chapters(self, test_client, test_db, editor_authenticated):
        """Test editor can create chapters"""
        token = editor_authenticated["access_token"]
        user = editor_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Editor's Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201

    def test_editor_can_update_any_chapter(self, test_client, test_db, editor_authenticated):
        """Test editor can update any chapter"""
        token = editor_authenticated["access_token"]

        other_user_id = generate_uuid()
        project = create_test_project(test_db, owner_id=other_user_id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "Updated by Editor"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_editor_can_lock_terms(self, test_client, test_db, editor_authenticated):
        """Test editor can lock terms"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Important Term")

        response = test_client.post(
            f"/api/terms/{term['id']}/lock",
            json={"reason": "Standardized definition"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_editor_cannot_delete_projects(self, test_client, test_db, editor_authenticated):
        """Test editor cannot delete projects"""
        token = editor_authenticated["access_token"]
        user = editor_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_editor_can_scan_content(self, test_client, test_db, editor_authenticated):
        """Test editor can scan content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={"content": "Test content to scan"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200


class TestReviewerPermissions:
    """Tests for reviewer role permissions"""

    def test_reviewer_can_approve_chapters(self, test_client, test_db, reviewer_authenticated):
        """Test reviewer can approve chapters"""
        token = reviewer_authenticated["access_token"]
        user = reviewer_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], status="reviewing")

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/approve",
            json={"comments": "Looks good", "chapter_id": chapter["id"]},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_reviewer_can_reject_chapters(self, test_client, test_db, reviewer_authenticated):
        """Test reviewer can reject chapters"""
        token = reviewer_authenticated["access_token"]
        user = reviewer_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], status="reviewing")

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/reject",
            json={"comments": "Needs revision", "chapter_id": chapter["id"]},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_reviewer_can_submit_for_review(self, test_client, test_db, reviewer_authenticated):
        """Test reviewer can submit chapters for review"""
        token = reviewer_authenticated["access_token"]
        user = reviewer_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/review",
            json={"chapter_id": chapter["id"], "comments": "Submitting for review"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_reviewer_cannot_create_chapters(self, test_client, test_db, reviewer_authenticated):
        """Test reviewer cannot create chapters"""
        token = reviewer_authenticated["access_token"]
        user = reviewer_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Reviewer's Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestAdminPermissions:
    """Tests for admin role permissions"""

    def test_admin_can_list_users(self, test_client, test_db, test_admin_authenticated):
        """Test admin can list users"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_admin_can_create_users(self, test_client, test_db, test_admin_authenticated):
        """Test admin can create users"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/admin/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "role": "viewer",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201

    def test_admin_can_update_user_roles(self, test_client, test_db, test_admin_authenticated):
        """Test admin can update user roles"""
        token = test_admin_authenticated["access_token"]
        test_admin_authenticated["user"]

        target_user = test_db.create_user(
            {
                "username": "targetuser",
                "email": "target@example.com",
                "password": "password123",
                "role": "viewer",
            }
        )

        response = test_client.put(
            f"/api/admin/users/{target_user.id}/role",
            json={"role": "author"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_admin_can_delete_users(self, test_client, test_db, test_admin_authenticated):
        """Test admin can delete users"""
        token = test_admin_authenticated["access_token"]
        test_admin_authenticated["user"]

        target_user = test_db.create_user(
            {
                "username": "todelete",
                "email": "todelete@example.com",
                "password": "password123",
                "role": "viewer",
            }
        )

        response = test_client.delete(
            f"/api/admin/users/{target_user.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_admin_cannot_delete_self(self, test_client, test_db, test_admin_authenticated):
        """Test admin cannot delete their own account"""
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

    def test_admin_can_view_roles(self, test_client, test_db, test_admin_authenticated):
        """Test admin can view all roles"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_admin_can_view_permissions(self, test_client, test_db, test_admin_authenticated):
        """Test admin can view all permissions"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_admin_can_get_stats(self, test_client, test_db, test_admin_authenticated):
        """Test admin can get admin statistics"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data["data"]
        assert "total_projects" in data["data"]


class TestPermissionHierarchy:
    """Tests for permission hierarchy enforcement"""

    def test_higher_role_can_do_lower_role_actions(self, test_client, test_db, test_admin_authenticated):
        """Test that higher roles can perform lower role actions"""
        token = test_admin_authenticated["access_token"]

        project = create_test_project(test_db, owner_id="any-user")

        response = test_client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_content_admin_can_manage_content(self, test_client, test_db, test_admin_authenticated):
        """Test content admin can manage content"""
        token = test_admin_authenticated["access_token"]
        user = test_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Admin Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201


class TestCrossRoleScenarios:
    """Tests for cross-role interaction scenarios"""

    def test_author_submits_reviewer_approves(self, test_client, test_db, author_authenticated, reviewer_authenticated):
        """Test author submits, reviewer approves workflow"""
        author_token = author_authenticated["access_token"]
        reviewer_token = reviewer_authenticated["access_token"]
        author_user = author_authenticated["user"]
        reviewer_authenticated["user"]

        project = create_test_project(test_db, owner_id=author_user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], author_id=author_user.id)

        submit_response = test_client.post(
            f"/api/chapters/{chapter['id']}/review",
            json={"chapter_id": chapter["id"], "comments": "Ready for review"},
            headers={
                "Authorization": f"Bearer {author_token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert submit_response.status_code == 200

        approve_response = test_client.post(
            f"/api/chapters/{chapter['id']}/approve",
            json={"comments": "Approved", "chapter_id": chapter["id"]},
            headers={
                "Authorization": f"Bearer {reviewer_token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert approve_response.status_code == 200

    def test_unauthorized_user_cannot_access_protected_resources(
        self,
        test_client,
    ):
        """Test unauthorized access is properly rejected"""
        protected_endpoints = [
            ("/api/projects", "get"),
            ("/api/projects", "post"),
            ("/api/chapters", "post"),
            ("/api/terms", "post"),
            ("/api/knowledge-graph/nodes", "post"),
            ("/api/security/scan", "post"),
            ("/api/monitor/metrics", "get"),
            ("/api/admin/users", "get"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "get":
                response = test_client.get(endpoint)
            else:
                response = test_client.post(
                    endpoint,
                    json={},
                    headers={"X-CSRF-Token": "test_csrf_token"},
                )

            assert response.status_code == 401, f"{method.upper()} {endpoint} should require auth"
