"""
Project Management API Integration Tests

Tests for project endpoints:
- GET /api/projects - List projects
- POST /api/projects - Create project
- GET /api/projects/{id} - Get project details
- PUT /api/projects/{id} - Update project
- DELETE /api/projects/{id} - Delete project
- POST /api/projects/{id}/members - Add project member
- GET /api/projects/{id}/stats - Get project statistics
- GET /api/projects/my/projects - List current user's projects
"""

import pytest
from datetime import datetime

from api.deps import generate_uuid, create_access_token
from tests.api.conftest import (
    create_test_project,
    create_test_chapter,
    create_test_user,
    get_auth_header,
    get_csrf_headers,
)


class TestListProjects:
    """Tests for listing projects"""

    def test_list_projects_empty(
        self, test_client, test_user_authenticated
    ):
        """Test listing projects when none exist"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_projects_with_data(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing projects with existing data"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        create_test_project(test_db, owner_id=user.id, name="Project 1")
        create_test_project(test_db, owner_id=user.id, name="Project 2")

        response = test_client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_list_projects_pagination(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test project listing with pagination"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        for i in range(5):
            create_test_project(test_db, owner_id=user.id, name=f"Project {i}")

        response = test_client.get(
            "/api/projects?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 5
        assert data["meta"]["total_pages"] == 3

    def test_list_projects_filter_by_status(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test filtering projects by status"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        create_test_project(test_db, owner_id=user.id, name="Draft Project", status="draft")
        create_test_project(test_db, owner_id=user.id, name="Active Project", status="active")

        response = test_client.get(
            "/api/projects?status_filter=active",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "active"

    def test_list_projects_unauthorized(self, test_client):
        """Test listing projects without authentication"""
        response = test_client.get("/api/projects")

        assert response.status_code == 401


class TestCreateProject:
    """Tests for creating projects"""

    def test_create_project(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successful project creation"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        response = test_client.post(
            "/api/projects",
            json={
                "name": "New Project",
                "description": "A test project",
                "total_chapters": 10,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "A test project"
        assert data["total_chapters"] == 10
        assert data["owner_id"] == user.id
        assert data["status"] == "draft"

    def test_create_project_minimal(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating project with minimal fields"""
        token = content_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/projects",
            json={
                "name": "Minimal Project",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"

    def test_create_project_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot create projects"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/projects",
            json={
                "name": "Unauthorized Project",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_create_project_no_name(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating project without name fails"""
        token = content_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/projects",
            json={
                "description": "Missing name",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 422


class TestGetProject:
    """Tests for getting project details"""

    def test_get_project(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting project by ID"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id, name="Test Project")

        response = test_client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project["id"]
        assert data["name"] == "Test Project"

    def test_get_project_not_found(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting non-existent project"""
        token = test_user_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/projects/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_project_unauthorized(self, test_client):
        """Test getting project without authentication"""
        response = test_client.get("/api/projects/some-id")

        assert response.status_code == 401


class TestUpdateProject:
    """Tests for updating projects"""

    def test_update_project(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating project details"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id, name="Original Name")

        response = test_client.put(
            f"/api/projects/{project['id']}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "status": "active",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["status"] == "active"

    def test_update_project_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating non-existent project"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.put(
            f"/api/projects/{fake_id}",
            json={"name": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_update_project_no_data(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating project with no data"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.put(
            f"/api/projects/{project['id']}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400

    def test_update_project_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot update projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.put(
            f"/api/projects/{project['id']}",
            json={"name": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestDeleteProject:
    """Tests for deleting projects"""

    def test_delete_project_owner(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test project owner can delete project"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_project_admin(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test admin can delete any project"""
        token = test_admin_authenticated["access_token"]
        admin = test_admin_authenticated["user"]

        other_user = test_db.create_user({
            "username": "otheruser",
            "email": "other@example.com",
            "password": "testpassword123",
            "role": "author",
        })
        project = create_test_project(test_db, owner_id=other_user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_delete_project_not_owner(
        self, test_client, test_db, author_authenticated
    ):
        """Test non-owner cannot delete project"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        other_user = test_db.create_user({
            "username": "otherowner",
            "email": "otherowner@example.com",
            "password": "testpassword123",
            "role": "author",
        })
        project = create_test_project(test_db, owner_id=other_user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_delete_project_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test deleting non-existent project"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.delete(
            f"/api/projects/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_project_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
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


class TestAddProjectMember:
    """Tests for adding project members"""

    def test_add_project_member(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test adding a member to project"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        new_member = test_db.create_user({
            "username": "newmember",
            "email": "newmember@example.com",
            "password": "testpassword123",
            "role": "author",
        })

        response = test_client.post(
            f"/api/projects/{project['id']}/members",
            json={
                "user_id": new_member.id,
                "role": "editor",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == new_member.id
        assert data["role"] == "editor"

    def test_add_project_member_user_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test adding non-existent user as member"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        fake_user_id = generate_uuid()

        response = test_client.post(
            f"/api/projects/{project['id']}/members",
            json={
                "user_id": fake_user_id,
                "role": "editor",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_add_project_member_project_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test adding member to non-existent project"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        new_member = test_db.create_user({
            "username": "member2",
            "email": "member2@example.com",
            "password": "testpassword123",
            "role": "author",
        })

        response = test_client.post(
            "/api/projects/nonexistent-id/members",
            json={
                "user_id": new_member.id,
                "role": "editor",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_add_project_member_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot add project members"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        new_member = test_db.create_user({
            "username": "member3",
            "email": "member3@example.com",
            "password": "testpassword123",
            "role": "author",
        })

        response = test_client.post(
            f"/api/projects/{project['id']}/members",
            json={
                "user_id": new_member.id,
                "role": "editor",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestGetProjectStats:
    """Tests for project statistics"""

    def test_get_project_stats(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting project statistics"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], status="published", word_count=1000)
        create_test_chapter(test_db, project_id=project["id"], status="draft", word_count=500)
        create_test_chapter(test_db, project_id=project["id"], status="reviewing", word_count=300)

        response = test_client.get(
            f"/api/projects/{project['id']}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_chapters"] == 3
        assert data["completed_chapters"] == 1
        assert data["draft_chapters"] == 1
        assert data["total_words"] == 1800

    def test_get_project_stats_not_found(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting stats for non-existent project"""
        token = test_user_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/projects/{fake_id}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_project_stats_empty_project(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting stats for project with no chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.get(
            f"/api/projects/{project['id']}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_chapters"] == 0
        assert data["total_words"] == 0


class TestListMyProjects:
    """Tests for listing current user's projects"""

    def test_list_my_projects(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing current user's projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        create_test_project(test_db, owner_id=user.id, name="My Project 1")
        create_test_project(test_db, owner_id=user.id, name="My Project 2")

        other_user = test_db.create_user({
            "username": "other",
            "email": "other@example.com",
            "password": "testpassword123",
            "role": "author",
        })
        create_test_project(test_db, owner_id=other_user.id, name="Other Project")

        response = test_client.get(
            "/api/projects/my/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        for project in data["data"]:
            assert project["owner_id"] == user.id

    def test_list_my_projects_empty(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing projects when user has none"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/projects/my/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    def test_list_my_projects_pagination(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test pagination of user's projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        for i in range(5):
            create_test_project(test_db, owner_id=user.id, name=f"My Project {i}")

        response = test_client.get(
            "/api/projects/my/projects?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 5

    def test_list_my_projects_unauthorized(self, test_client):
        """Test listing user's projects without authentication"""
        response = test_client.get("/api/projects/my/projects")

        assert response.status_code == 401


class TestProjectEdgeCases:
    """Edge case tests for projects"""

    def test_list_projects_second_page(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting second page of projects"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        for i in range(5):
            create_test_project(test_db, owner_id=user.id, name=f"Project {i}")

        response = test_client.get(
            "/api/projects?page=2&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["page"] == 2

    def test_create_project_all_statuses(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating projects - all default to draft status"""
        token = content_admin_authenticated["access_token"]

        for i, status in enumerate(["draft", "active", "completed", "archived"]):
            response = test_client.post(
                "/api/projects",
                json={
                    "name": f"Project Status {i}",
                    "status": status,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "draft"

    def test_update_project_status_only(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating only project status"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id, status="draft")

        response = test_client.put(
            f"/api/projects/{project['id']}",
            json={"status": "active"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["name"] == project["name"]

    def test_get_project_with_chapters(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting project details with chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 1")
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 2")

        response = test_client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project["id"]


class TestDeleteProjectPermission:
    """Tests for delete project permission branch (line 203)"""

    def test_delete_project_owner_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test owner can delete their own project (line 202 branch)"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_project_admin_bypass(
        self, test_client, test_db, test_admin_authenticated
    ):
        """Test system_admin can delete any project (line 203 branch)"""
        token = test_admin_authenticated["access_token"]

        other_user = test_db.create_user({
            "username": "otherowner",
            "email": "otherowner@example.com",
            "password": "testpassword123",
            "role": "author",
        })
        project = create_test_project(test_db, owner_id=other_user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_project_non_owner_forbidden(
        self, test_client, test_db, author_authenticated
    ):
        """Test non-owner cannot delete project"""
        token = author_authenticated["access_token"]

        other_user = test_db.create_user({
            "username": "projectowner",
            "email": "projectowner@example.com",
            "password": "testpassword123",
            "role": "author",
        })
        project = create_test_project(test_db, owner_id=other_user.id)

        response = test_client.delete(
            f"/api/projects/{project['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "PERMISSION_DENIED"
