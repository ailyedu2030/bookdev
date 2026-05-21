"""
Term and Glossary API Integration Tests

Tests for term endpoints:
- GET /api/terms - List terms
- POST /api/terms - Create term
- PUT /api/terms/{id} - Update term
- POST /api/terms/{id}/lock - Lock term
- POST /api/terms/search - Search terms
"""

import pytest
from datetime import datetime

from api.deps import generate_uuid
from tests.api.conftest import create_test_term, get_auth_header, get_csrf_headers


class TestListTerms:
    """Tests for listing terms"""

    def test_list_terms_empty(self, test_client, test_db, test_user_authenticated):
        """Test listing terms when none exist"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/terms",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    def test_list_terms_with_data(self, test_client, test_db, test_user_authenticated):
        """Test listing terms with existing data"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Python", definition="A programming language")
        create_test_term(test_db, term="FastAPI", definition="A web framework")

        response = test_client.get(
            "/api/terms",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 2

    def test_list_terms_filter_by_domain(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing terms filtered by domain"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Python", domain="programming")
        create_test_term(test_db, term="FastAPI", domain="programming")
        create_test_term(test_db, term="Physics", domain="science")

        response = test_client.get(
            "/api/terms?domain=programming",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert all(t["domain"] == "programming" for t in data["data"])

    def test_list_terms_filter_by_locked(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test listing terms filtered by lock status"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Python", locked=False)
        create_test_term(test_db, term="FastAPI", locked=True)

        response = test_client.get(
            "/api/terms?locked=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["locked"] is True

    def test_list_terms_pagination(self, test_client, test_db, test_user_authenticated):
        """Test term listing with pagination"""
        token = test_user_authenticated["access_token"]

        for i in range(5):
            create_test_term(test_db, term=f"Term {i}", definition=f"Definition {i}")

        response = test_client.get(
            "/api/terms?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_list_terms_unauthorized(self, test_client):
        """Test listing terms without authentication"""
        response = test_client.get("/api/terms")

        assert response.status_code == 401


class TestCreateTerm:
    """Tests for creating terms"""

    def test_create_term(self, test_client, test_db, author_authenticated):
        """Test successful term creation"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Machine Learning",
                "definition": "A subset of AI that enables systems to learn",
                "domain": "artificial_intelligence",
                "synonyms": ["ML", "Statistical Learning"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "Machine Learning"
        assert data["definition"] == "A subset of AI that enables systems to learn"
        assert data["domain"] == "artificial_intelligence"
        assert data["synonyms"] == ["ML", "Statistical Learning"]
        assert data["locked"] is False
        assert data["version"] == 1

    def test_create_term_minimal(self, test_client, test_db, author_authenticated):
        """Test term creation with minimal data"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Test Term",
                "definition": "A test definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "Test Term"

    def test_create_term_empty_term(self, test_client, test_db, author_authenticated):
        """Test creating term with empty term name fails"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "",
                "definition": "A definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 422

    def test_create_term_empty_definition(
        self, test_client, test_db, author_authenticated
    ):
        """Test creating term with empty definition fails"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Test Term",
                "definition": "",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 422

    def test_create_term_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot create terms"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/terms",
            json={
                "term": "Unauthorized Term",
                "definition": "A definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestGetTerm:
    """Tests for getting term details"""

    def test_get_term(self, test_client, test_db, test_user_authenticated):
        """Test getting term by ID"""
        token = test_user_authenticated["access_token"]

        term = create_test_term(test_db, term="Python", definition="Programming language")

        response = test_client.get(
            f"/api/terms/{term['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == term["id"]
        assert data["term"] == "Python"

    def test_get_term_not_found(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test getting non-existent term"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/terms/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestUpdateTerm:
    """Tests for updating terms"""

    def test_update_term(self, test_client, test_db, author_authenticated):
        """Test updating term details"""
        token = author_authenticated["access_token"]

        term = create_test_term(
            test_db, term="Python", definition="Original definition"
        )

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={
                "term": "Updated Python",
                "definition": "Updated definition",
                "synonyms": ["New Synonym"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "Updated Python"
        assert data["definition"] == "Updated definition"
        assert data["synonyms"] == ["New Synonym"]

    def test_update_locked_term(self, test_client, test_db, author_authenticated):
        """Test cannot update locked term"""
        token = author_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Term", locked=True)

        response = test_client.put(
            f"/api/terms/{term['id']}",
            json={"term": "Attempt to update"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "TERM_LOCKED"

    def test_update_term_not_found(
        self, test_client, test_db, author_authenticated
    ):
        """Test updating non-existent term"""
        token = author_authenticated["access_token"]

        response = test_client.put(
            "/api/terms/nonexistent-id",
            json={"term": "Updated Term"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestLockTerm:
    """Tests for locking terms"""

    def test_lock_term(self, test_client, test_db, editor_authenticated):
        """Test locking a term"""
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
        data = response.json()
        assert data["locked"] is True
        assert data["lock_reason"] == "Standardized definition"

    def test_lock_term_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test locking non-existent term"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/nonexistent-id/lock",
            json={"reason": "Test reason"},
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


class TestUnlockTerm:
    """Tests for unlocking terms"""

    def test_unlock_term(self, test_client, test_db, editor_authenticated):
        """Test unlocking a term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Term", locked=True)

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


class TestSearchTerms:
    """Tests for searching terms"""

    def test_search_terms_by_term(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test searching terms by term name"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Python Programming", definition="Python lang")
        create_test_term(test_db, term="JavaScript", definition="JS language")
        create_test_term(test_db, term="Pythonista", definition="Python lover")

        response = test_client.post(
            "/api/terms/search",
            json={"query": "Python", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        terms_found = [t["term"] for t in data["data"]]
        assert "Python Programming" in terms_found
        assert "Pythonista" in terms_found
        assert "JavaScript" not in terms_found

    def test_search_terms_by_definition(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test searching terms by definition content"""
        token = test_user_authenticated["access_token"]

        create_test_term(
            test_db, term="AI", definition="Artificial Intelligence simulation"
        )
        create_test_term(test_db, term="ML", definition="Machine Learning")

        response = test_client.post(
            "/api/terms/search",
            json={"query": "Intelligence", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["term"] == "AI"

    def test_search_terms_by_synonym(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test searching terms by synonym"""
        token = test_user_authenticated["access_token"]

        create_test_term(
            test_db, term="Machine Learning", synonyms=["ML", "Statistical Learning"]
        )

        response = test_client.post(
            "/api/terms/search",
            json={"query": "ML", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["term"] == "Machine Learning"

    def test_search_terms_with_domain_filter(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test searching terms with domain filter"""
        token = test_user_authenticated["access_token"]

        create_test_term(
            test_db, term="Python", domain="programming", definition="Lang"
        )
        create_test_term(
            test_db, term="Snake", domain="biology", definition="Animal"
        )

        response = test_client.post(
            "/api/terms/search",
            json={"query": "Python", "domain": "programming", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["domain"] == "programming"

    def test_search_terms_empty_query(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test searching with empty query fails"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/terms/search",
            json={"query": "", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422


class TestDeleteTerm:
    """Tests for deleting terms"""

    def test_delete_term(self, test_client, test_db, editor_authenticated):
        """Test deleting term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="To Delete")

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

    def test_delete_locked_term(self, test_client, test_db, editor_authenticated):
        """Test cannot delete locked term"""
        token = editor_authenticated["access_token"]

        term = create_test_term(test_db, term="Locked Delete", locked=True)

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


class TestListDomains:
    """Tests for listing term domains"""

    def test_list_domains(self, test_client, test_db, test_user_authenticated):
        """Test listing all unique domains"""
        token = test_user_authenticated["access_token"]

        create_test_term(test_db, term="Python", domain="programming")
        create_test_term(test_db, term="FastAPI", domain="programming")
        create_test_term(test_db, term="Physics", domain="science")

        response = test_client.get(
            "/api/terms/domains/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "programming" in data
        assert "science" in data
        assert len(data) == 2
