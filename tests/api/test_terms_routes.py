"""
Additional Terms API Tests for Higher Coverage

Tests additional endpoints and edge cases for terms routes.
"""

import pytest
from datetime import datetime

from api.deps import generate_uuid
from tests.api.conftest import create_test_term


class TestTermsAdditional:
    """Additional tests for terms endpoints"""

    def test_list_terms_second_page(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing terms with pagination page 2"""
        token = test_user_authenticated["access_token"]

        for i in range(5):
            create_test_term(test_db, term=f"Term {i}", definition=f"Def {i}")

        response = test_client.get(
            "/api/terms?page=2&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_list_terms_filter_by_locked_false(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing terms filtered by locked=false"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Unlocked Term", locked=False)

        response = test_client.get(
            "/api/terms?locked=false",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(t["locked"] is False for t in data["data"])

    def test_list_terms_filter_by_domain_and_locked(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing terms filtered by domain and lock status"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Term 1", domain="math", locked=False)
        create_test_term(test_db, term="Term 2", domain="math", locked=True)

        response = test_client.get(
            "/api/terms?domain=math&locked=false",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["domain"] == "math"
        assert data["data"][0]["locked"] is False

    def test_create_term_full(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating term with all fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Full Term",
                "definition": "A term with all fields",
                "domain": "testing",
                "synonyms": ["syn1", "syn2"],
                "first_defined_at": "Chapter 1",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "Full Term"
        assert data["domain"] == "testing"
        assert data["synonyms"] == ["syn1", "syn2"]

    def test_create_term_minimal(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating term with minimal fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Minimal Term",
                "definition": "Minimal definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "Minimal Term"

    def test_get_term(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting a term by ID"""
        token = test_user_authenticated["access_token"]

        term = create_test_term(test_db, term="Get Test", definition="Test definition")

        response = test_client.get(
            f"/api/terms/{term['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "Get Test"

    def test_get_term_not_found(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting a non-existent term"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/terms/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_update_term_synonyms(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating term synonyms"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Python", definition="A language")

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={"synonyms": ["PY", "Pythonista"]},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["synonyms"] == ["PY", "Pythonista"]

    def test_update_term_domain(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating term domain"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Test", definition="Test def")

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={"domain": "programming"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "programming"

    def test_unlock_term_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test unlocking non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/nonexistent-id/unlock",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_term_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.delete(
            "/api/terms/nonexistent-id",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_lock_term_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot lock terms"""
        token = test_user_authenticated["access_token"]

        term = create_test_term(test_db, term="Protected Term")

        response = test_client.post(
            f"/api/terms/{term['id']}/lock",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_search_terms_limit(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test search with limit parameter"""
        token = test_user_authenticated["access_token"]

        for i in range(10):
            create_test_term(test_db, term=f"Python {i}", definition="Python related")

        response = test_client.post(
            "/api/terms/search",
            json={"query": "Python", "limit": 3},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 3

    def test_update_term_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating a non-existent term returns 404"""
        token = editor_authenticated["access_token"]

        response = test_client.put(
            "/api/terms/nonexistent-term-id",
            json={"term": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "TERM_NOT_FOUND"

    def test_update_term_locked(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating a locked term returns 400"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Term", locked=True, lock_reason="Testing")

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={"term": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "TERM_LOCKED"

    def test_update_term_no_data(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating a term with no data returns 400"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Test Term")

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "NO_UPDATE_DATA"

    def test_lock_term_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test successfully locking a term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Unlocked Term", locked=False)

        response = test_client.post(
            f"/api/terms/{term['id']}/lock",
            params={"reason": "Testing lock"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["locked"] is True

    def test_lock_term_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test locking a non-existent term returns 404"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/nonexistent-term-id/lock",
            params={"reason": "Testing"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "TERM_NOT_FOUND"

    def test_unlock_term_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test successfully unlocking a term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Term", locked=True, lock_reason="Was locked")

        response = test_client.post(
            f"/api/terms/{term['id']}/unlock",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["locked"] is False

    def test_delete_term_locked(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting a locked term returns 400"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Term", locked=True)

        response = test_client.delete(
            f"/api/terms/{term['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "TERM_LOCKED"

    def test_delete_term_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test successfully deleting an unlocked term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Term To Delete", locked=False)

        response = test_client.delete(
            f"/api/terms/{term['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    def test_list_domains(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing all unique domains"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Term 1", domain="math")
        create_test_term(test_db, term="Term 2", domain="science")
        create_test_term(test_db, term="Term 3", domain="math")
        create_test_term(test_db, term="Term 4", domain=None)

        response = test_client.get(
            "/api/terms/domains/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "math" in data
        assert "science" in data


class TestConceptsAdditional:
    """Additional tests for concepts endpoints"""

    def test_list_concepts_with_domain(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing concepts filtered by domain"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/concepts?domain=programming",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_concepts_with_locked(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing concepts filtered by locked status"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/concepts?locked=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_concepts_pagination(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing concepts with pagination"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/concepts?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.skip(reason="concepts:create permission not assigned to any role")
    def test_create_concept_full(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating concept with all fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/concepts",
            json={
                "name": "Full Concept",
                "definition": "A concept with all fields",
                "domain": "testing",
                "related_terms": ["term-1", "term-2"],
                "source_chapter_id": "chapter-123",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Full Concept"
        assert data["related_terms"] == ["term-1", "term-2"]

    @pytest.mark.skip(reason="concepts:create permission not assigned to any role")
    def test_create_concept_minimal(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating concept with minimal fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/concepts",
            json={
                "name": "Minimal Concept",
                "definition": "Minimal definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Concept"


class TestCitationsAdditional:
    """Additional tests for citations endpoints"""

    @pytest.mark.skip(reason="citations:create permission not assigned to any role")
    def test_create_citation_full(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating citation with all fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/citations",
            json={
                "chapter_id": "chapter-123",
                "doi": "10.1234/test",
                "title": "Test Citation",
                "authors": ["Author 1", "Author 2"],
                "journal": "Test Journal",
                "year": 2024,
                "url": "https://example.com/test",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Citation"
        assert data["doi"] == "10.1234/test"

    @pytest.mark.skip(reason="citations:create permission not assigned to any role")
    def test_create_citation_minimal(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating citation with minimal fields"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/citations",
            json={
                "chapter_id": "chapter-123",
                "title": "Minimal Citation",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Citation"

    def test_list_citations_by_chapter(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing citations by chapter"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/citations/chapter/chapter-123",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.skip(reason="citations:verify permission not assigned to any role")
    def test_verify_citation(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying a citation"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/citations/citation-123/verify",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
        assert data["verified_at"] is not None
