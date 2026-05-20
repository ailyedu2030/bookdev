"""
Security API Integration Tests

Tests for security endpoints:
- POST /api/security/scan - Content safety scan
- POST /api/security/doi/verify - DOI verification
- POST /api/security/regulation/verify - Regulation verification
- POST /api/security/semantic/scan - Semantic scan
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from tests.api.conftest import get_auth_header, get_csrf_headers


class TestContentScan:
    """Tests for content safety scanning"""

    def test_security_scan_safe_content(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning safe content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={
                "content": "This is a sample textbook content about programming.",
                "categories": ["profanity", "hate_speech"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "is_safe" in data
        assert "confidence_score" in data

    def test_security_scan_with_pii(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning content with PII categories"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={
                "content": "Contact John at john@example.com",
                "categories": ["pii"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_security_scan_empty_content(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning empty content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={"content": ""},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_security_scan_unauthorized(self, test_client):
        """Test scanning without authentication"""
        response = test_client.post(
            "/api/security/scan",
            json={"content": "Test content"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )

        assert response.status_code == 401

    def test_security_scan_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot scan content"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/security/scan",
            json={"content": "Test content"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestDOIVerification:
    """Tests for DOI verification"""

    def test_doi_verification_valid(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying valid DOI"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/doi/verify",
            json={"doi": "10.1234/example"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "valid" in data
        assert data["doi"] == "10.1234/example"

    def test_doi_verification_invalid(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying invalid DOI format"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/doi/verify",
            json={"doi": "not-a-doi"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_doi_verification_missing(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying without DOI"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/doi/verify",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 422

    def test_doi_verification_unauthorized(self, test_client):
        """Test DOI verification without authentication"""
        response = test_client.post(
            "/api/security/doi/verify",
            json={"doi": "10.1234/test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )

        assert response.status_code == 401

    def test_doi_verification_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot verify DOI"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/security/doi/verify",
            json={"doi": "10.1234/test"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestRegulationVerification:
    """Tests for regulation verification"""

    def test_regulation_verification_valid(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying content against regulations"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/regulation/verify",
            json={
                "content": "This textbook content follows academic standards.",
                "law_type": "academic_integrity",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "valid" in data
        assert "matched_laws" in data
        assert "confidence" in data

    def test_regulation_verification_empty_content(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying empty content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/regulation/verify",
            json={"content": ""},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_regulation_verification_unauthorized(self, test_client):
        """Test regulation verification without authentication"""
        response = test_client.post(
            "/api/security/regulation/verify",
            json={"content": "Test content"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )

        assert response.status_code == 401

    def test_regulation_verification_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot verify regulations"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/security/regulation/verify",
            json={"content": "Test content"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestSemanticScan:
    """Tests for semantic scanning"""

    def test_semantic_scan_consistent_content(
        self, test_client, test_db, editor_authenticated
    ):
        """Test scanning consistent content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/semantic/scan",
            json={
                "content": "Machine learning is a subset of artificial intelligence. "
                "It enables systems to learn from data.",
                "threshold": 0.7,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "issues" in data
        assert "score" in data
        assert "summary" in data

    def test_semantic_scan_with_threshold(
        self, test_client, test_db, editor_authenticated
    ):
        """Test semantic scan with custom threshold"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/semantic/scan",
            json={
                "content": "Python is a programming language. Java is a programming language.",
                "threshold": 0.5,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_semantic_scan_empty_threshold(
        self, test_client, test_db, editor_authenticated
    ):
        """Test semantic scan with empty content"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/semantic/scan",
            json={"content": "", "threshold": 0.7},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200

    def test_semantic_scan_unauthorized(self, test_client):
        """Test semantic scan without authentication"""
        response = test_client.post(
            "/api/security/semantic/scan",
            json={"content": "Test content"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )

        assert response.status_code == 401

    def test_semantic_scan_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot perform semantic scan"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/security/semantic/scan",
            json={"content": "Test content"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestMaterialSecurity:
    """Tests for material security registration"""

    def test_register_material(
        self, test_client, test_db, editor_authenticated
    ):
        """Test registering material with content hash"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/material/register",
            params={"content_hash": "abc123def456"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_verify_material(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying registered material"""
        token = editor_authenticated["access_token"]

        test_client.post(
            "/api/security/material/register",
            params={"content_hash": "verified_hash_123"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        response = test_client.get(
            "/api/security/material/verify/verified_hash_123",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "registered" in data
        assert "verified" in data

    def test_verify_material_unregistered(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying unregistered material"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/security/material/verify/unregistered_hash",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["registered"] is False


class TestBatchScan:
    """Tests for batch content scanning"""

    def test_batch_scan(
        self, test_client, test_db, editor_authenticated
    ):
        """Test batch scanning multiple contents"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/batch/scan",
            json={
                "contents": [
                    "First piece of content",
                    "Second piece of content",
                    "Third piece of content",
                ]
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert "safe_count" in data
        assert "unsafe_count" in data
        assert len(data["results"]) == 3

    def test_batch_scan_empty_list(
        self, test_client, test_db, editor_authenticated
    ):
        """Test batch scanning with empty list"""
        token = editor_authenticated["access_token"]

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


class TestConceptIntegrity:
    """Tests for concept integrity verification"""

    def test_verify_concept_integrity(
        self, test_client, test_db, editor_authenticated
    ):
        """Test verifying concept integrity"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/security/concept/verify",
            json={
                "concept_id": "concept-123",
                "definition": "A verified concept definition",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "valid" in data
        assert "integrity_score" in data
