"""Tests for api/routes/chapters.py"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.deps import User, DatabaseSession


def run_async(coro):
    """Run async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestListChapters:
    """Test list chapters endpoint."""

    def test_list_chapters_success(self):
        """Test successful chapter listing."""
        from api.routes.chapters import list_chapters

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123"}
        mock_db.list_chapters_by_project.return_value = [
            {"id": "c1", "title": "Chapter 1", "status": "draft", "project_id": "project-123", "order_num": 1, "word_count": 0, "content": "", "content_hash": "abc", "version": "1.0", "created_at": "2024-01-01T00:00:00"},
            {"id": "c2", "title": "Chapter 2", "status": "published", "project_id": "project-123", "order_num": 2, "word_count": 1000, "content": "content", "content_hash": "def", "version": "1.0", "created_at": "2024-01-02T00:00:00"},
        ]

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(list_chapters(
                "project-123", page=1, per_page=20, status_filter=None, user=mock_user, db=mock_db
            ))

            assert result.success is True
            assert len(result.data) == 2

    def test_list_chapters_project_not_found(self):
        """Test list chapters fails when project doesn't exist."""
        from api.routes.chapters import list_chapters

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = None

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(list_chapters(
                    "nonexistent", page=1, per_page=20, status_filter=None, user=mock_user, db=mock_db
                ))

            assert exc_info.value.status_code == 404
            assert "PROJECT_NOT_FOUND" in str(exc_info.value.detail)


class TestCreateChapter:
    """Test create chapter endpoint."""

    def test_create_chapter_success(self):
        """Test successful chapter creation."""
        from api.routes.chapters import create_chapter
        from api.schemas.chapter import ChapterCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_project.return_value = {"id": "project-123"}
        mock_db.create_chapter.return_value = {
            "id": "new-chapter-id",
            "title": "New Chapter",
            "status": "draft",
            "project_id": "project-123",
            "order_num": 1,
            "word_count": 0,
            "content": "",
            "content_hash": "abc",
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
        }

        chapter_data = ChapterCreate(
            project_id="project-123",
            title="New Chapter",
            order_num=1,
        )

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(create_chapter(chapter_data, mock_user, mock_db))

            assert result.title == "New Chapter"


class TestGetChapter:
    """Test get chapter endpoint."""

    def test_get_chapter_success(self):
        """Test successful chapter retrieval."""
        from api.routes.chapters import get_chapter

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {
            "id": "chapter-123",
            "title": "Test Chapter",
            "status": "draft",
            "project_id": "project-123",
            "order_num": 1,
            "word_count": 0,
            "content": "",
            "content_hash": "abc",
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
        }

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(get_chapter("chapter-123", mock_user, mock_db))

            assert result.id == "chapter-123"

    def test_get_chapter_not_found(self):
        """Test get chapter fails when chapter doesn't exist."""
        from api.routes.chapters import get_chapter

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = None

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_chapter("nonexistent", mock_user, mock_db))

            assert exc_info.value.status_code == 404


class TestUpdateChapter:
    """Test update chapter endpoint."""

    def test_update_chapter_success(self):
        """Test successful chapter update."""
        from api.routes.chapters import update_chapter
        from api.schemas.chapter import ChapterUpdate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {
            "id": "chapter-123",
            "title": "Old Title",
            "status": "draft",
            "project_id": "project-123",
            "order_num": 1,
            "word_count": 0,
            "content": "",
            "content_hash": "abc",
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
        }
        mock_db.update_chapter.return_value = {
            "id": "chapter-123",
            "title": "New Title",
            "status": "draft",
            "project_id": "project-123",
            "order_num": 1,
            "word_count": 0,
            "content": "",
            "content_hash": "abc",
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
        }

        update_data = ChapterUpdate(title="New Title")

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            with patch('api.routes.chapters.hash_content', return_value="hash123"):
                result = run_async(update_chapter("chapter-123", update_data, mock_user, mock_db))

                assert result.title == "New Title"


class TestDeleteChapter:
    """Test delete chapter endpoint."""

    def test_delete_chapter_success(self):
        """Test successful chapter deletion."""
        from api.routes.chapters import delete_chapter

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.delete_chapter.return_value = True

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(delete_chapter("chapter-123", mock_user, mock_db))

            assert result.success is True


class TestSubmitForReview:
    """Test submit for review endpoint."""

    def test_submit_for_review_success(self):
        """Test successful review submission."""
        from api.routes.chapters import submit_for_review
        from api.schemas.chapter import ReviewSubmit

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.update_chapter.return_value = {"id": "chapter-123", "status": "reviewing"}

        review_data = ReviewSubmit(chapter_id="chapter-123", comments="Please review")

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(submit_for_review("chapter-123", review_data, mock_user, mock_db))

            assert result.status == "submitted"


class TestApproveChapter:
    """Test approve chapter endpoint."""

    def test_approve_chapter_success(self):
        """Test successful chapter approval."""
        from api.routes.chapters import approve_chapter
        from api.schemas.chapter import ReviewApprove

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="reviewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.update_chapter.return_value = {"id": "chapter-123", "status": "approved"}

        approval_data = ReviewApprove(chapter_id="chapter-123", comments="Approved")

        with patch('api.routes.chapters.require_role', return_value=lambda u: u):
            result = run_async(approve_chapter("chapter-123", approval_data, mock_user, mock_db))

            assert result.status == "approved"


class TestRejectChapter:
    """Test reject chapter endpoint."""

    def test_reject_chapter_success(self):
        """Test successful chapter rejection."""
        from api.routes.chapters import reject_chapter
        from api.schemas.chapter import ReviewReject

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="reviewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.update_chapter.return_value = {"id": "chapter-123", "status": "rejected"}

        rejection_data = ReviewReject(chapter_id="chapter-123", comments="Needs revision")

        with patch('api.routes.chapters.require_role', return_value=lambda u: u):
            result = run_async(reject_chapter("chapter-123", rejection_data, mock_user, mock_db))

            assert result.status == "rejected"


class TestCreateSection:
    """Test create section endpoint."""

    def test_create_section_success(self):
        """Test successful section creation."""
        from api.routes.chapters import create_section
        from api.schemas.chapter import SectionCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.create_section.return_value = {
            "id": "section-123",
            "chapter_id": "chapter-123",
            "title": "New Section",
            "order_num": 1,
            "status": "draft",
            "word_count": 0,
            "parent_section_id": None,
            "created_at": "2025-01-01T00:00:00",
        }

        section_data = SectionCreate(
            chapter_id="chapter-123",
            title="New Section",
            order_num=1,
        )

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(create_section(section_data, mock_user, mock_db))

            assert result.title == "New Section"
            assert result.chapter_id == "chapter-123"


class TestGenerateChapterContent:
    """Test generate chapter content endpoint."""

    def test_generate_content_success(self):
        """Test successful content generation trigger."""
        from api.routes.chapters import generate_chapter_content
        from api.schemas.chapter import ChapterGenerateRequest
        from unittest.mock import MagicMock

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_chapter.return_value = {"id": "chapter-123"}
        mock_db.update_chapter.return_value = {"id": "chapter-123", "status": "generating"}

        mock_background = MagicMock()
        mock_background.add_task = MagicMock()

        request = ChapterGenerateRequest(chapter_id="chapter-123", prompt="Generate content", force_regenerate=False)

        with patch('api.routes.chapters.require_permission', return_value=lambda u: u):
            result = run_async(generate_chapter_content(
                "chapter-123", request, mock_background, mock_user, mock_db
            ))

            assert result.status == "generating"
            mock_background.add_task.assert_called_once()