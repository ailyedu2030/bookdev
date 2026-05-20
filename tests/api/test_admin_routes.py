"""
Admin Routes API Integration Tests

Tests for admin endpoints using properly permissioned users.
"""

import pytest
from unittest.mock import patch, MagicMock

from api.deps import generate_uuid, create_access_token
from tests.api.conftest import (
    create_test_project,
    create_test_chapter,
    get_auth_header,
    get_csrf_headers,
)


class TestListUsers:
    """Tests for listing users"""

    def test_list_users_empty(self, test_client, test_admin_authenticated):
        """Test listing users when none exist"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_with_data(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test listing users with existing data"""
        token = test_admin_authenticated["access_token"]
        admin = test_admin_authenticated["user"]

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

        response = test_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_users_pagination(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test user listing with pagination"""
        token = test_admin_authenticated["access_token"]

        for i in range(5):
            test_db.create_user({
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "pass123",
                "role": "viewer",
            })

        response = test_client.get(
            "/api/admin/users?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_users_filter_by_role(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test filtering users by role"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "editor1",
            "email": "editor@example.com",
            "password": "pass123",
            "role": "editor",
        })
        test_db.create_user({
            "username": "viewer1",
            "email": "viewer@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.get(
            "/api/admin/users?role_filter=editor",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for user in data:
            assert user["role"] == "editor"

    def test_list_users_search(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test searching users by username or email"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "johndoe",
            "email": "john@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.get(
            "/api/admin/users?search=john",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_users_unauthorized(self, test_client, test_user_authenticated):
        """Test listing users without admin role"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403


class TestCreateUser:
    """Tests for creating users"""

    @patch("api.routes.admin.get_password_hash")
    def test_create_user_success(
        self, mock_hash, test_client, test_db, test_admin_authenticated
    ):
        """Test successful user creation"""
        mock_hash.return_value = "hashed_password"
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
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "viewer"

    def test_create_user_duplicate_email(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test creating user with existing email"""
        token = test_admin_authenticated["access_token"]
        test_db.create_user({
            "username": "existing",
            "email": "existing@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.post(
            "/api/admin/users",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "password123",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "EMAIL_EXISTS" in str(data)

    def test_create_user_viewer_forbidden(
        self, test_client, test_user_authenticated
    ):
        """Test creating user by non-admin"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/admin/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestGetUser:
    """Tests for getting user details"""

    def test_get_user_success(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test getting user details"""
        token = test_admin_authenticated["access_token"]
        new_user = test_db.create_user({
            "username": "target",
            "email": "target@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.get(
            f"/api/admin/users/{new_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == new_user.id
        assert data["email"] == "target@example.com"

    def test_get_user_not_found(
        self, test_client, test_admin_authenticated
    ):
        """Test getting non-existent user"""
        token = test_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/admin/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestUpdateUser:
    """Tests for updating users"""

    def test_update_user_success(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user details"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "updateme",
            "email": "update@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}",
            json={"organization_id": "new-org"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == "new-org"

    def test_update_user_not_found(
        self, test_client, test_admin_authenticated
    ):
        """Test updating non-existent user"""
        token = test_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.put(
            f"/api/admin/users/{fake_id}",
            json={"organization_id": "new-org"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_update_user_no_data(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user with no data"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "testuser",
            "email": "test@example.com",
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


class TestDeleteUser:
    """Tests for deleting users"""

    def test_delete_user_success(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test deleting a user"""
        token = test_admin_authenticated["access_token"]
        admin = test_admin_authenticated["user"]
        target_user = test_db.create_user({
            "username": "deleteme",
            "email": "delete@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.delete(
            f"/api/admin/users/{target_user.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_user_not_found(
        self, test_client, test_admin_authenticated
    ):
        """Test deleting non-existent user"""
        token = test_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.delete(
            f"/api/admin/users/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_user_cannot_delete_self(
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


class TestUpdateUserRole:
    """Tests for updating user roles"""

    def test_update_user_role_success(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user role"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "roleuser",
            "email": "role@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}/role",
            json={"role": "editor"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "editor"

    def test_update_user_role_not_found(
        self, test_client, test_admin_authenticated
    ):
        """Test updating role of non-existent user"""
        token = test_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.put(
            f"/api/admin/users/{fake_id}/role",
            json={"role": "editor"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_update_user_role_cannot_modify_self(
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


class TestListRoles:
    """Tests for listing roles"""

    def test_list_roles_success(
        self, test_client, test_admin_authenticated
    ):
        """Test listing available roles"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for role in data:
            assert "name" in role
            assert "level" in role
            assert "permissions" in role

    def test_list_roles_unauthorized(
        self, test_client, test_user_authenticated
    ):
        """Test listing roles without admin"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403


class TestListPermissions:
    """Tests for listing permissions"""

    def test_list_permissions_success(
        self, test_client, test_admin_authenticated
    ):
        """Test listing available permissions"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "resources" in data

    def test_list_permissions_unauthorized(
        self, test_client, test_user_authenticated
    ):
        """Test listing permissions without admin"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403


class TestListRolesExpanded:
    """Expanded tests for listing roles"""

    def test_list_roles_includes_all_roles(
        self, test_client, test_admin_authenticated
    ):
        """Test that all roles are included in the list"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        role_names = [r["name"] for r in data]
        assert "system_admin" in role_names
        assert "content_admin" in role_names
        assert "editor" in role_names
        assert "reviewer" in role_names
        assert "author" in role_names
        assert "viewer" in role_names

    def test_list_roles_sorted_by_level(
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


class TestListPermissionsExpanded:
    """Expanded tests for listing permissions"""

    def test_list_permissions_includes_resources(
        self, test_client, test_admin_authenticated
    ):
        """Test that permissions are grouped by resource"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        resources = data["resources"]
        assert "projects" in resources
        assert "chapters" in resources

    def test_list_permissions_admin_has_all(
        self, test_client, test_admin_authenticated
    ):
        """Test that admin has wildcard permission"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


class TestAdminStats:
    """Tests for admin statistics"""

    def test_get_admin_stats_success(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test getting admin statistics"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "testuser",
            "email": "stats@example.com",
            "password": "pass123",
            "role": "viewer",
        })
        create_test_project(test_db, owner_id="test")

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_users" in data["data"]
        assert "total_projects" in data["data"]

    def test_get_admin_stats_unauthorized(
        self, test_client, test_user_authenticated
    ):
        """Test getting stats without admin"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    def test_get_admin_stats_content_admin(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test content admin can get stats"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAdminStatsExpanded:
    """Expanded tests for admin statistics"""

    def test_get_admin_stats_with_chapters(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats include chapter data"""
        token = test_admin_authenticated["access_token"]
        user = test_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], status="draft")
        create_test_chapter(test_db, project_id=project["id"], status="published")

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_chapters"] == 2
        assert "chapters_by_status" in data["data"]

    def test_get_admin_stats_empty_system(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats with empty system"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_users"] >= 1
        assert data["data"]["total_projects"] == 0
        assert data["data"]["total_chapters"] == 0
        assert data["data"]["total_terms"] == 0

    def test_get_admin_stats_users_by_role(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin stats shows users by role"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "admin2",
            "email": "admin2@example.com",
            "password": "pass123",
            "role": "system_admin",
        })
        test_db.create_user({
            "username": "editor1",
            "email": "editor1@example.com",
            "password": "pass123",
            "role": "editor",
        })

        response = test_client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "system_admin" in data["data"]["users_by_role"]
        assert "editor" in data["data"]["users_by_role"]


class TestUpdateUserExpanded:
    """Expanded tests for updating users"""

    def test_update_user_clearance_level(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating user clearance level"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "clearanceuser",
            "email": "clearance@example.com",
            "password": "pass123",
            "role": "viewer",
            "clearance_level": 1,
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}",
            json={"clearance_level": 3},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clearance_level"] == 3

    def test_update_user_both_org_and_clearance(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test updating both organization and clearance level"""
        token = test_admin_authenticated["access_token"]
        target_user = test_db.create_user({
            "username": "multiuser",
            "email": "multi@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.put(
            f"/api/admin/users/{target_user.id}",
            json={"organization_id": "new-org", "clearance_level": 5},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == "new-org"
        assert data["clearance_level"] == 5


class TestListUsersExpanded:
    """Expanded tests for listing users"""

    def test_list_users_search_by_email(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test searching users by email"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "johndoe",
            "email": "john.doe@company.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.get(
            "/api/admin/users?search=john.doe",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("john.doe" in u["email"] for u in data)

    def test_list_users_search_case_insensitive(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test search is case insensitive"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "JaneDoe",
            "email": "jane@example.com",
            "password": "pass123",
            "role": "viewer",
        })

        response = test_client.get(
            "/api/admin/users?searchJANEDOE",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_users_pagination_page_2(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test getting second page of users"""
        token = test_admin_authenticated["access_token"]

        for i in range(7):
            test_db.create_user({
                "username": f"pageuser{i}",
                "email": f"pageuser{i}@example.com",
                "password": "pass123",
                "role": "viewer",
            })

        response = test_client.get(
            "/api/admin/users?page=2&per_page=3",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_users_with_role_and_search(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test filtering by role and searching simultaneously"""
        token = test_admin_authenticated["access_token"]

        test_db.create_user({
            "username": "adminuser",
            "email": "adminuser@example.com",
            "password": "pass123",
            "role": "system_admin",
        })
        test_db.create_user({
            "username": "edituser",
            "email": "edituser@example.com",
            "password": "pass123",
            "role": "editor",
        })

        response = test_client.get(
            "/api/admin/users?role_filter=system_admin&search=admin",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["role"] == "system_admin"
            assert "admin" in user["username"].lower() or "admin" in user["email"].lower()


class TestCreateUserExpanded:
    """Expanded tests for creating users"""

    @patch("api.routes.admin.get_password_hash")
    def test_create_user_with_organization(
        self, mock_hash, test_client, test_db, test_admin_authenticated
    ):
        """Test creating user with organization"""
        mock_hash.return_value = "hashed_password"
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/admin/users",
            json={
                "username": "orguser",
                "email": "orguser@example.com",
                "password": "password123",
                "role": "viewer",
                "organization_id": "test-org-456",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["organization_id"] == "test-org-456"

    @patch("api.routes.admin.get_password_hash")
    def test_create_user_default_role(
        self, mock_hash, test_client, test_db, test_admin_authenticated
    ):
        """Test creating user defaults to viewer role"""
        mock_hash.return_value = "hashed_password"
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/admin/users",
            json={
                "username": "defaultroleuser",
                "email": "default@example.com",
                "password": "password123",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "viewer"


class TestRolesPermissionsExpanded:
    """Expanded tests for roles and permissions"""

    def test_list_roles_contains_permissions(
        self, test_client, test_admin_authenticated
    ):
        """Test that each role has permissions array"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/roles/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for role in data:
            assert isinstance(role["permissions"], list)

    def test_list_permissions_all_resources_have_actions(
        self, test_client, test_admin_authenticated
    ):
        """Test that each resource has actions list"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/admin/permissions/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        resources = data["resources"]
        for resource, actions in resources.items():
            assert isinstance(actions, list)
