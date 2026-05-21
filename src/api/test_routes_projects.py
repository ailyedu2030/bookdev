"""Tests for api/routes/projects.py"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.deps import DatabaseSession, User


def run_async(coro):
    """Run async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestListProjects:
    """Test list projects endpoint."""

    def test_list_projects_success(self):
        """Test successful project listing."""
        from api.routes.projects import list_projects

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_projects.return_value = [
            {"id": "p1", "name": "Project 1", "status": "active", "description": "", "total_chapters": 5, "owner_id": "user-123", "created_at": "2024-01-01T00:00:00"},
            {"id": "p2", "name": "Project 2", "status": "draft", "description": "", "total_chapters": 3, "owner_id": "user-123", "created_at": "2024-01-02T00:00:00"},
        ]

        result = run_async(list_projects(
            page=1, per_page=20, status_filter=None, user=mock_user, db=mock_db
        ))

        assert result.success is True
        assert len(result.data) == 2
        assert result.meta["total"] == 2

    def test_list_projects_with_filter(self):
        """Test project listing with status filter."""
        from api.routes.projects import list_projects

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_projects.return_value = [
            {"id": "p1", "name": "Project 1", "status": "active", "description": "", "total_chapters": 5, "owner_id": "user-123", "created_at": "2024-01-01T00:00:00"},
            {"id": "p2", "name": "Project 2", "status": "active", "description": "", "total_chapters": 3, "owner_id": "user-123", "created_at": "2024-01-02T00:00:00"},
            {"id": "p3", "name": "Project 3", "status": "draft", "description": "", "total_chapters": 2, "owner_id": "user-123", "created_at": "2024-01-03T00:00:00"},
        ]

        result = run_async(list_projects(
            page=1, per_page=20, status_filter="active", user=mock_user, db=mock_db
        ))

        assert result.success is True
        assert len(result.data) == 2
        assert all(p.status == "active" for p in result.data)


class TestCreateProject:
    """Test create project endpoint."""

    def test_create_project_success(self):
        """Test successful project creation."""
        from api.routes.projects import create_project
        from api.schemas.project import ProjectCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.create_project.return_value = {
            "id": "new-project-id",
            "name": "New Project",
            "description": "A new project",
            "status": "draft",
            "owner_id": "user-123",
            "total_chapters": 10,
            "created_at": "2024-01-01T00:00:00",
        }

        project_data = ProjectCreate(
            name="New Project",
            description="A new project",
            total_chapters=10,
        )

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(create_project(project_data, mock_user, mock_db))

            assert result.name == "New Project"
            assert result.status == "draft"


class TestGetProject:
    """Test get project endpoint."""

    def test_get_project_success(self):
        """Test successful project retrieval."""
        from api.routes.projects import get_project

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {
            "id": "project-123",
            "name": "Test Project",
            "status": "active",
            "description": "",
            "total_chapters": 5,
            "owner_id": "user-123",
            "created_at": "2024-01-01T00:00:00",
        }

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(get_project("project-123", mock_user, mock_db))

            assert result.id == "project-123"
            assert result.name == "Test Project"

    def test_get_project_not_found(self):
        """Test project retrieval when project doesn't exist."""
        from api.routes.projects import get_project

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = None

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_project("nonexistent", mock_user, mock_db))

            assert exc_info.value.status_code == 404
            assert "PROJECT_NOT_FOUND" in str(exc_info.value.detail)


class TestUpdateProject:
    """Test update project endpoint."""

    def test_update_project_success(self):
        """Test successful project update."""
        from api.routes.projects import update_project
        from api.schemas.project import ProjectUpdate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123", "name": "Old Name", "status": "draft", "description": "", "total_chapters": 5, "owner_id": "user-123", "created_at": "2024-01-01T00:00:00"}
        mock_db.update_project.return_value = {"id": "project-123", "name": "New Name", "status": "active", "description": "", "total_chapters": 5, "owner_id": "user-123", "created_at": "2024-01-01T00:00:00"}

        update_data = ProjectUpdate(name="New Name")

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(update_project("project-123", update_data, mock_user, mock_db))

            assert result.name == "New Name"

    def test_update_project_not_found(self):
        """Test update fails when project doesn't exist."""
        from api.routes.projects import update_project
        from api.schemas.project import ProjectUpdate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = None

        update_data = ProjectUpdate(name="New Name")

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(update_project("nonexistent", update_data, mock_user, mock_db))

            assert exc_info.value.status_code == 404


class TestDeleteProject:
    """Test delete project endpoint."""

    def test_delete_project_success(self):
        """Test successful project deletion."""
        from api.routes.projects import delete_project

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123", "owner_id": "user-123"}
        mock_db.delete_project.return_value = True

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(delete_project("project-123", mock_user, mock_db))

            assert result.success is True

    def test_delete_project_not_owner(self):
        """Test delete fails when user is not the owner."""
        from api.routes.projects import delete_project

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123", "owner_id": "other-user"}

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_project("project-123", mock_user, mock_db))

            assert exc_info.value.status_code == 403


class TestAddProjectMember:
    """Test add project member endpoint."""

    def test_add_member_success(self):
        """Test successful member addition."""
        from api.routes.projects import add_project_member
        from api.schemas.project import ProjectMemberAdd

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123"}
        mock_db.get_user_by_id.return_value = MagicMock(
            id="member-456",
            username="newmember",
            email="member@example.com",
        )

        member_data = ProjectMemberAdd(user_id="member-456", role="editor")

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(add_project_member("project-123", member_data, mock_user, mock_db))

            assert result.project_id == "project-123"
            assert result.user_id == "member-456"


class TestGetProjectStats:
    """Test get project stats endpoint."""

    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        from api.routes.projects import get_project_stats

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123"}
        mock_db.list_chapters_by_project.return_value = [
            {"status": "published", "word_count": 1000},
            {"status": "published", "word_count": 2000},
            {"status": "generating", "word_count": 0},
        ]

        with patch('api.routes.projects.require_permission', return_value=lambda u: u):
            result = run_async(get_project_stats("project-123", mock_user, mock_db))

            assert result.total_chapters == 3
            assert result.completed_chapters == 2
            assert result.total_words == 3000


class TestListMyProjects:
    """Test list my projects endpoint."""

    def test_list_my_projects_success(self):
        """Test successful retrieval of user's projects."""
        from api.routes.projects import list_my_projects

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_projects.return_value = [
            {"id": "p1", "name": "My Project 1", "status": "draft", "description": "", "total_chapters": 5, "owner_id": "user-123", "created_at": "2024-01-01T00:00:00"},
            {"id": "p2", "name": "My Project 2", "status": "active", "description": "", "total_chapters": 3, "owner_id": "user-123", "created_at": "2024-01-02T00:00:00"},
        ]

        result = run_async(list_my_projects(page=1, per_page=20, user=mock_user, db=mock_db))

        assert result.success is True
        assert len(result.data) == 2
