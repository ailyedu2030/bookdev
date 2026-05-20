"""Tests for api/routes/terms.py"""

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


class TestListTerms:
    """Test list terms endpoint."""

    def test_list_terms_success(self):
        """Test successful term listing."""
        from api.routes.terms import list_terms

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_terms.return_value = [
            {"id": "t1", "term": "Term1", "definition": "Def1", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"},
            {"id": "t2", "term": "Term2", "definition": "Def2", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-02T00:00:00"},
        ]

        result = run_async(list_terms(
            domain=None, locked=None, page=1, per_page=20, user=mock_user, db=mock_db
        ))

        assert result.success is True
        assert len(result.data) == 2

    def test_list_terms_with_locked_filter(self):
        """Test term listing with locked filter."""
        from api.routes.terms import list_terms

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_terms.return_value = [
            {"id": "t1", "term": "Term1", "definition": "Def1", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"},
            {"id": "t2", "term": "Term2", "definition": "Def2", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-02T00:00:00"},
            {"id": "t3", "term": "Term3", "definition": "Def3", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-03T00:00:00"},
        ]

        result = run_async(list_terms(
            domain=None, locked=True, page=1, per_page=20, user=mock_user, db=mock_db
        ))

        assert result.success is True
        assert len(result.data) == 2


class TestCreateTerm:
    """Test create term endpoint."""

    def test_create_term_success(self):
        """Test successful term creation."""
        from api.routes.terms import create_term
        from api.schemas.term import TermCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.create_term.return_value = {
            "id": "new-term-id",
            "term": "NewTerm",
            "definition": "New definition",
            "domain": "testing",
            "synonyms": [],
            "locked": False,
            "created_at": "2024-01-01T00:00:00",
        }

        term_data = TermCreate(
            term="NewTerm",
            definition="New definition",
            domain="testing",
            synonyms=[],
        )

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(create_term(term_data, mock_user, mock_db))

            assert result.term == "NewTerm"
            assert result.locked is False


class TestGetTerm:
    """Test get term endpoint."""

    def test_get_term_success(self):
        """Test successful term retrieval."""
        from api.routes.terms import get_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {
            "id": "term-123",
            "term": "TestTerm",
            "definition": "Test definition",
            "domain": "test",
            "synonyms": [],
            "locked": False,
            "created_at": "2024-01-01T00:00:00",
        }

        result = run_async(get_term("term-123", mock_user, mock_db))

        assert result.id == "term-123"
        assert result.term == "TestTerm"

    def test_get_term_not_found(self):
        """Test term retrieval when term doesn't exist."""
        from api.routes.terms import get_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            run_async(get_term("nonexistent", mock_user, mock_db))

        assert exc_info.value.status_code == 404
        assert "TERM_NOT_FOUND" in str(exc_info.value.detail)


class TestUpdateTerm:
    """Test update term endpoint."""

    def test_update_term_success(self):
        """Test successful term update."""
        from api.routes.terms import update_term
        from api.schemas.term import TermUpdate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "Old", "definition": "Old def", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"}
        mock_db.update_term.return_value = {"id": "term-123", "term": "New", "definition": "Old def", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"}

        update_data = TermUpdate(term="New")

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(update_term("term-123", update_data, mock_user, mock_db))

            assert result.term == "New"

    def test_update_locked_term_fails(self):
        """Test update fails for locked term."""
        from api.routes.terms import update_term
        from api.schemas.term import TermUpdate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "Locked", "definition": "Def", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-01T00:00:00"}

        update_data = TermUpdate(term="New")

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(update_term("term-123", update_data, mock_user, mock_db))

            assert exc_info.value.status_code == 400
            assert "TERM_LOCKED" in str(exc_info.value.detail)


class TestLockTerm:
    """Test lock term endpoint."""

    def test_lock_term_success(self):
        """Test successful term locking."""
        from api.routes.terms import lock_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "ToLock", "definition": "Def", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"}
        mock_db.lock_term.return_value = {"id": "term-123", "term": "ToLock", "definition": "Def", "domain": "test", "synonyms": [], "locked": True, "lock_reason": "Dispute", "created_at": "2024-01-01T00:00:00"}

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(lock_term("term-123", "Dispute", mock_user, mock_db))

            assert result.locked is True


class TestUnlockTerm:
    """Test unlock term endpoint."""

    def test_unlock_term_success(self):
        """Test successful term unlocking."""
        from api.routes.terms import unlock_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "Locked", "definition": "Def", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-01T00:00:00"}
        mock_db.update_term.return_value = {"id": "term-123", "term": "Locked", "definition": "Def", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"}

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(unlock_term("term-123", mock_user, mock_db))

            assert result.locked is False


class TestDeleteTerm:
    """Test delete term endpoint."""

    def test_delete_term_success(self):
        """Test successful term deletion."""
        from api.routes.terms import delete_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "ToDelete", "definition": "Def", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"}
        mock_db.delete_term.return_value = True

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(delete_term("term-123", mock_user, mock_db))

            assert result.success is True

    def test_delete_locked_term_fails(self):
        """Test delete fails for locked term."""
        from api.routes.terms import delete_term

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_term.return_value = {"id": "term-123", "term": "Locked", "definition": "Def", "domain": "test", "synonyms": [], "locked": True, "created_at": "2024-01-01T00:00:00"}

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_term("term-123", mock_user, mock_db))

            assert exc_info.value.status_code == 400


class TestSearchTerms:
    """Test search terms endpoint."""

    def test_search_terms_success(self):
        """Test successful term search."""
        from api.routes.terms import search_terms
        from api.schemas.term import TermSearchRequest

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_terms.return_value = [
            {"id": "t1", "term": "TestTerm", "definition": "A test term", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-01T00:00:00"},
            {"id": "t2", "term": "Other", "definition": "Something else", "domain": "test", "synonyms": [], "locked": False, "created_at": "2024-01-02T00:00:00"},
        ]

        request = TermSearchRequest(query="Test", domain=None, limit=10)

        result = run_async(search_terms(request, mock_user, mock_db))

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].term == "TestTerm"


class TestListDomains:
    """Test list domains endpoint."""

    def test_list_domains_success(self):
        """Test successful domain listing."""
        from api.routes.terms import list_domains

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.list_terms.return_value = [
            {"domain": "science"},
            {"domain": "math"},
            {"domain": "science"},
        ]

        result = run_async(list_domains(mock_user, mock_db))

        assert "math" in result
        assert "science" in result


class TestCreateConcept:
    """Test create concept endpoint."""

    def test_create_concept_success(self):
        """Test successful concept creation."""
        from api.routes.terms import create_concept
        from api.schemas.term import ConceptCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        concept_data = ConceptCreate(
            name="New Concept",
            definition="Concept definition",
            domain="testing",
        )

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(create_concept(concept_data, mock_user, mock_db))

            assert result.name == "New Concept"
            assert result.locked is False


class TestCreateCitation:
    """Test create citation endpoint."""

    def test_create_citation_success(self):
        """Test successful citation creation."""
        from api.routes.terms import create_citation
        from api.schemas.term import CitationCreate

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        citation_data = CitationCreate(
            chapter_id="chapter-123",
            doi="10.1234/test",
            title="Test Citation",
            authors=["Author 1"],
            journal="Test Journal",
            year=2024,
        )

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(create_citation(citation_data, mock_user, mock_db))

            assert result.title == "Test Citation"
            assert result.verified is False


class TestVerifyCitation:
    """Test verify citation endpoint."""

    def test_verify_citation_success(self):
        """Test successful citation verification."""
        from api.routes.terms import verify_citation

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="reviewer",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        with patch('api.routes.terms.require_permission', return_value=lambda u: u):
            result = run_async(verify_citation("citation-123", mock_user, mock_db))

            assert result.verified is True
            assert result.id == "citation-123"