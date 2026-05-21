"""
Security Routes Comprehensive Tests - 100% Coverage Target

Tests all endpoints in src/api/routes/security.py.
Focuses on mock mode (ImportError paths) since real modules have different APIs.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from tests.api.conftest import get_auth_header, get_csrf_headers


class TestContentScanMockMode:
    """Test scan_content mock mode - when module import fails"""

    def test_scan_content_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test scan_content when module import fails (mock mode)"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
            response = test_client.post(
                "/api/security/scan",
                json={"content": "Test content"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_safe"] is True
        assert data["confidence_score"] == 1.0
        assert data["categories"] == ["mock"]
        assert data["action"] == "PASS"

    def test_scan_content_mock_mode_empty(self, test_client, test_db, content_admin_authenticated):
        """Test scan_content empty content in mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
            response = test_client.post(
                "/api/security/scan",
                json={"content": ""},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200

    def test_scan_content_mock_mode_with_categories(self, test_client, test_db, content_admin_authenticated):
        """Test scan_content with categories in mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
            response = test_client.post(
                "/api/security/scan",
                json={
                    "content": "Test content",
                    "categories": ["profanity", "hate_speech", "pii", "political", "injection"],
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDOIVerifyMockMode:
    """Test DOI verification mock mode"""

    def test_doi_verify_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test DOI verification when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f07_doi_verification': None,
            'f07_doi_verification.doi_verifier': None,
        }):
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
        assert data["success"] is True
        assert data["valid"] is True
        assert data["doi"] == "10.1234/test"
        assert data["metadata"]["title"] == "Mock Citation"
        assert data["metadata"]["authors"] == ["Author 1", "Author 2"]

    def test_doi_verify_mock_mode_different_dois(self, test_client, test_db, content_admin_authenticated):
        """Test DOI verification with various DOIs in mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f07_doi_verification': None,
            'f07_doi_verification.doi_verifier': None,
        }):
            for doi in ["10.1000/xyz", "10.1038/nature", "10.1126/science"]:
                response = test_client.post(
                    "/api/security/doi/verify",
                    json={"doi": doi},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-CSRF-Token": "test_csrf_token",
                    },
                )
                assert response.status_code == 200
                assert response.json()["doi"] == doi


class TestRegulationVerifyMockMode:
    """Test regulation verification mock mode"""

    def test_regulation_verify_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test regulation verification when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f08_regulation_verification': None,
            'f08_regulation_verification.regulation_verifier': None,
        }):
            response = test_client.post(
                "/api/security/regulation/verify",
                json={"content": "Test content", "law_type": "copyright"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["valid"] is True
        assert data["confidence"] == 0.95

    def test_regulation_verify_mock_mode_empty_content(self, test_client, test_db, content_admin_authenticated):
        """Test regulation verification with empty content"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f08_regulation_verification': None,
            'f08_regulation_verification.regulation_verifier': None,
        }):
            response = test_client.post(
                "/api/security/regulation/verify",
                json={"content": ""},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200

    def test_regulation_verify_mock_mode_no_law_type(self, test_client, test_db, content_admin_authenticated):
        """Test regulation verification without law_type"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f08_regulation_verification': None,
            'f08_regulation_verification.regulation_verifier': None,
        }):
            response = test_client.post(
                "/api/security/regulation/verify",
                json={"content": "Test content"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200


class TestSemanticScanMockMode:
    """Test semantic scan mock mode"""

    def test_semantic_scan_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test semantic scan when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f13_global_semantic_scanner': None,
            'f13_global_semantic_scanner.semantic_scanner': None,
        }):
            response = test_client.post(
                "/api/security/semantic/scan",
                json={"content": "Test content", "threshold": 0.8},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["score"] == 1.0
        assert data["issues"] == []

    def test_semantic_scan_mock_mode_no_threshold(self, test_client, test_db, content_admin_authenticated):
        """Test semantic scan without threshold parameter"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f13_global_semantic_scanner': None,
            'f13_global_semantic_scanner.semantic_scanner': None,
        }):
            response = test_client.post(
                "/api/security/semantic/scan",
                json={"content": "Content without threshold"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200


class TestMaterialRegisterMockMode:
    """Test material registration mock mode"""

    def test_register_material_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test material registration when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f09_material_security': None,
            'f09_material_security.source_registry': None,
        }):
            response = test_client.post(
                "/api/security/material/register",
                params={
                    "content_hash": "test_hash_123",
                    "source_url": "https://example.com",
                    "copyright_info": "CC BY 4.0",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_register_material_mock_mode_minimal(self, test_client, test_db, content_admin_authenticated):
        """Test material registration with only content_hash"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f09_material_security': None,
            'f09_material_security.source_registry': None,
        }):
            response = test_client.post(
                "/api/security/material/register",
                params={"content_hash": "min_hash"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200


class TestMaterialVerifyMockMode:
    """Test material verification mock mode"""

    def test_verify_material_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test material verification when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f09_material_security': None,
            'f09_material_security.source_registry': None,
        }):
            response = test_client.get(
                "/api/security/material/verify/nonexistent_hash",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["registered"] is False
        assert data["verified"] is True


class TestConceptVerifyMockMode:
    """Test concept integrity verification mock mode"""

    def test_verify_concept_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test concept verification when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f10_concept_security': None,
            'f10_concept_security.integrity_verifier': None,
        }):
            response = test_client.post(
                "/api/security/concept/verify",
                json={
                    "concept_id": "concept-123",
                    "definition": "A test definition",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["valid"] is True
        assert data["integrity_score"] == 1.0

    def test_verify_concept_mock_mode_multiple(self, test_client, test_db, content_admin_authenticated):
        """Test multiple concept verifications in mock mode"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f10_concept_security': None,
            'f10_concept_security.integrity_verifier': None,
        }):
            concepts = [
                ("concept-1", "Definition one"),
                ("concept-2", "Definition two"),
            ]
            for concept_id, definition in concepts:
                response = test_client.post(
                    "/api/security/concept/verify",
                    json={"concept_id": concept_id, "definition": definition},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-CSRF-Token": "test_csrf_token",
                    },
                )
                assert response.status_code == 200


class TestBatchScanMockMode:
    """Test batch scanning mock mode"""

    def test_batch_scan_mock_mode(self, test_client, test_db, content_admin_authenticated):
        """Test batch scan when module import fails"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
            response = test_client.post(
                "/api/security/batch/scan",
                json={"contents": ["Content 1", "Content 2", "Content 3"]},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert data["safe_count"] == 3
        assert data["unsafe_count"] == 0

    def test_batch_scan_mock_mode_empty(self, test_client, test_db, content_admin_authenticated):
        """Test batch scan with empty list"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
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
        assert data["safe_count"] == 0
        assert data["unsafe_count"] == 0

    def test_batch_scan_mock_mode_long_content(self, test_client, test_db, content_admin_authenticated):
        """Test batch scan with content exceeding 100 chars"""
        token = content_admin_authenticated["access_token"]

        with patch.dict('sys.modules', {
            'f23_content_security': None,
            'f23_content_security.content_filter': None,
        }):
            response = test_client.post(
                "/api/security/batch/scan",
                json={"contents": ["A" * 150]},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "A" * 100 + "..." in data["results"][0]["content_preview"]


class TestSecurityAuthorization:
    """Test authorization and authentication for security endpoints"""

    def test_scan_unauthorized(self, test_client):
        """Test scan without authentication"""
        response = test_client.post(
            "/api/security/scan",
            json={"content": "Test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_doi_verify_unauthorized(self, test_client):
        """Test DOI verify without authentication"""
        response = test_client.post(
            "/api/security/doi/verify",
            json={"doi": "10.1234/test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_regulation_verify_unauthorized(self, test_client):
        """Test regulation verify without authentication"""
        response = test_client.post(
            "/api/security/regulation/verify",
            json={"content": "Test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_semantic_scan_unauthorized(self, test_client):
        """Test semantic scan without authentication"""
        response = test_client.post(
            "/api/security/semantic/scan",
            json={"content": "Test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_material_verify_unauthorized(self, test_client):
        """Test material verify without authentication"""
        response = test_client.get("/api/security/material/verify/some_hash")
        assert response.status_code == 401

    def test_batch_scan_unauthorized(self, test_client):
        """Test batch scan without authentication"""
        response = test_client.post(
            "/api/security/batch/scan",
            json={"contents": ["Test"]},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_concept_verify_unauthorized(self, test_client):
        """Test concept verify without authentication"""
        response = test_client.post(
            "/api/security/concept/verify",
            json={"concept_id": "c1", "definition": "test"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 401

    def test_viewer_forbidden_scan(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot scan"""
        token = test_user_authenticated["access_token"]
        response = test_client.post(
            "/api/security/scan",
            json={"content": "Test"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 403

    def test_viewer_forbidden_doi(self, test_client, test_db, test_user_authenticated):
        """Test viewer role cannot verify DOI"""
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


class TestSecurityValidation:
    """Test validation for security endpoints"""

    def test_doi_missing(self, test_client, test_db, content_admin_authenticated):
        """Test DOI verification with missing DOI field"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/security/doi/verify",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response.status_code == 422

    def test_scan_missing_content(self, test_client, test_db, content_admin_authenticated):
        """Test scan with missing content field - should accept empty/default"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/security/scan",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        # ScanRequest.content is Optional[str] with default="", so empty body is valid
        assert response.status_code == 200

    def test_semantic_scan_missing_content(self, test_client, test_db, content_admin_authenticated):
        """Test semantic scan with missing content field - should accept empty/default"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/security/semantic/scan",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        # SemanticScanRequest.content is Optional[str] with default="", so empty body is valid
        assert response.status_code == 200

    def test_regulation_verify_missing_content(self, test_client, test_db, content_admin_authenticated):
        """Test regulation verify with missing content field - should accept empty/default"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/security/regulation/verify",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        # RegulationVerifyRequest.content is Optional[str] with default="", so empty body is valid
        assert response.status_code == 200
