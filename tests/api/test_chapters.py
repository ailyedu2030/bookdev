"""
Chapter Management API Integration Tests

Tests for chapter endpoints:
- GET /api/chapters/{project_id} - List chapters
- POST /api/chapters - Create chapter
- GET /api/chapters/detail/{id} - Get chapter details
- PUT /api/chapters/{id} - Update chapter
- DELETE /api/chapters/{id} - Delete chapter
- POST /api/chapters/{id}/review - Submit for review
- POST /api/chapters/{id}/approve - Approve chapter
- POST /api/chapters/{id}/reject - Reject chapter
"""


from tests.api.conftest import (
    create_test_chapter,
    create_test_project,
    create_test_section,
)


class TestListChapters:
    """Tests for listing chapters"""

    def test_list_chapters_empty(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters when none exist"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.get(
            f"/api/chapters/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_chapters_with_data(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters with existing data"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 1")
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 2")

        response = test_client.get(
            f"/api/chapters/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_list_chapters_project_not_found(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters for non-existent project"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/chapters/nonexistent-project",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_list_chapters_filtered_by_status(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters filtered by status"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], title="Draft", status="draft")
        create_test_chapter(test_db, project_id=project["id"], title="Published", status="published")

        response = test_client.get(
            f"/api/chapters/{project['id']}?status_filter=published",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "published"


class TestCreateChapter:
    """Tests for creating chapters"""

    def test_create_chapter(self, test_client, test_db, author_authenticated):
        """Test successful chapter creation"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "New Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Chapter"
        assert data["order_num"] == 1
        assert data["project_id"] == project["id"]
        assert data["status"] == "draft"

    def test_create_chapter_with_parent(self, test_client, test_db, author_authenticated):
        """Test creating chapter with parent chapter"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        parent_chapter = create_test_chapter(test_db, project_id=project["id"], title="Parent")

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": project["id"],
                "title": "Child Chapter",
                "order_num": 1,
                "parent_chapter_id": parent_chapter["id"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_chapter_id"] == parent_chapter["id"]

    def test_create_chapter_project_not_found(self, test_client, test_db, author_authenticated):
        """Test creating chapter for non-existent project"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters",
            json={
                "project_id": "nonexistent-project",
                "title": "New Chapter",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_create_chapter_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
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


class TestGetChapter:
    """Tests for getting chapter details"""

    def test_get_chapter(self, test_client, test_db, test_user_authenticated):
        """Test getting chapter by ID"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], title="Test Chapter")

        response = test_client.get(
            f"/api/chapters/detail/{chapter['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == chapter["id"]
        assert data["title"] == "Test Chapter"

    def test_get_chapter_not_found(self, test_client, test_db, test_user_authenticated):
        """Test getting non-existent chapter"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/chapters/detail/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestUpdateChapter:
    """Tests for updating chapters"""

    def test_update_chapter(self, test_client, test_db, author_authenticated):
        """Test updating chapter details"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], title="Original Title")

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "Updated Title", "content": "New content here"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_chapter_content_hash(self, test_client, test_db, author_authenticated):
        """Test updating chapter content generates content hash"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"content": "Test content"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content_hash"] is not None
        assert data["word_count"] == len("Test content")

    def test_update_chapter_not_found(self, test_client, test_db, author_authenticated):
        """Test updating non-existent chapter"""
        token = author_authenticated["access_token"]

        response = test_client.put(
            "/api/chapters/nonexistent-id",
            json={"title": "Updated Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestDeleteChapterViewerForbidden:
    """Expanded tests for chapter deletion authorization"""

    def test_delete_chapter_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot delete chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.delete(
            f"/api/chapters/{chapter['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_delete_chapter_content_admin(self, test_client, test_db, content_admin_authenticated):
        """Test content admin can delete any chapter"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.delete(
            f"/api/chapters/{chapter['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200


class TestChapterUpdateExpanded:
    """Expanded tests for chapter updates"""

    def test_update_chapter_title_only(self, test_client, test_db, author_authenticated):
        """Test updating only chapter title"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], title="Original Title")

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "New Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"

    def test_update_chapter_status_only(self, test_client, test_db, author_authenticated):
        """Test updating only chapter status"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"status": "reviewing"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewing"

    def test_update_chapter_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot update chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "New Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestChapterPagination:
    """Tests for chapter list pagination"""

    def test_list_chapters_pagination_second_page(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters on second page"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        for i in range(25):
            create_test_chapter(test_db, project_id=project["id"], title=f"Chapter {i}")

        response = test_client.get(
            f"/api/chapters/{project['id']}?page=2&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 2
        assert data["meta"]["per_page"] == 10
        assert data["meta"]["total"] == 25
        assert data["meta"]["total_pages"] == 3
        assert len(data["data"]) == 10

    def test_list_chapters_pagination_partial_last_page(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters on partial last page"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        for i in range(23):
            create_test_chapter(test_db, project_id=project["id"], title=f"Chapter {i}")

        response = test_client.get(
            f"/api/chapters/{project['id']}?page=3&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 3
        assert len(data["data"]) == 3

    def test_list_chapters_pagination_single_page(self, test_client, test_db, test_user_authenticated):
        """Test listing chapters when all fit on one page"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 1")

        response = test_client.get(
            f"/api/chapters/{project['id']}?page=1&per_page=20",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total_pages"] == 1
        assert len(data["data"]) == 1


class TestChapterUpdateContent:
    """Tests for chapter content updates"""

    def test_update_chapter_with_content_generates_hash(self, test_client, test_db, author_authenticated):
        """Test updating chapter with content generates content_hash and word_count"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        test_content = "This is test content with multiple words."
        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"content": test_content},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content_hash"] is not None
        assert data["word_count"] == len(test_content)

    def test_update_chapter_with_title_and_content(self, test_client, test_db, author_authenticated):
        """Test updating chapter with both title and content"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"], title="Original Title")

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={"title": "New Title", "content": "New content here"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content_hash"] is not None


class TestChapterGenerateSuccess:
    """Tests for successful AI content generation - covers lines 283-311"""

    def test_generate_chapter_content_success(self, test_client, test_db, test_admin_authenticated):
        """Test successfully triggering AI content generation"""
        token = test_admin_authenticated["access_token"]
        user = test_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/generate",
            json={"chapter_id": chapter["id"], "prompt": "Generate content about topic X"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chapter_id"] == chapter["id"]
        assert data["status"] == "generating"
        assert "generation_id" in data

    def test_generate_chapter_with_force_regenerate(self, test_client, test_db, test_admin_authenticated):
        """Test triggering AI content generation with force_regenerate flag"""
        token = test_admin_authenticated["access_token"]
        user = test_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/generate",
            json={"chapter_id": chapter["id"], "prompt": "Regenerate content", "force_regenerate": True},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generating"


class TestChapterNotFoundCoverage:
    """Tests for 404 coverage in chapter operations - covers lines 239, 283-293"""

    def test_generate_chapter_chapter_not_found(self, test_client, test_db, test_admin_authenticated):
        """Test generate with non-existent chapter returns 404"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/nonexistent-id/generate",
            json={"chapter_id": "nonexistent-id", "prompt": "Generate"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestReviewWorkflowCoverage:
    """Tests for review workflow - covers lines 360-374, 401-415, 442-456"""

    def test_submit_for_review_chapter_not_found(self, test_client, test_db, reviewer_authenticated):
        """Test submit for review with non-existent chapter returns 404"""
        token = reviewer_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/nonexistent-id/review",
            json={"chapter_id": "nonexistent-id", "comments": "Ready"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_approve_chapter_not_found(self, test_client, test_db, reviewer_authenticated):
        """Test approve with non-existent chapter returns 404"""
        token = reviewer_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/nonexistent-id/approve",
            json={"chapter_id": "nonexistent-id", "comments": "Approved"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_reject_chapter_not_found(self, test_client, test_db, reviewer_authenticated):
        """Test reject with non-existent chapter returns 404"""
        token = reviewer_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/nonexistent-id/reject",
            json={"chapter_id": "nonexistent-id", "comments": "Rejected"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestContentVersionsCoverage:
    """Tests for content versions - covers lines 475-487"""

    def test_list_content_versions_chapter_not_found(self, test_client, test_db, test_user_authenticated):
        """Test list versions with non-existent chapter returns 404"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/chapters/nonexistent-id/versions",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestCreateSectionCoverage:
    """Tests for section creation - covers lines 520-540"""

    def test_create_section_chapter_not_found_returns_404(self, test_client, test_db, author_authenticated):
        """Test create section with non-existent chapter returns 404"""
        token = author_authenticated["access_token"]

        response = test_client.post(
            "/api/chapters/sections",
            json={
                "chapter_id": "nonexistent-chapter",
                "title": "New Section",
                "order_num": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestUpdateSectionNoData:
    """Tests for update section with no data - covers line 574"""

    def test_update_section_no_update_data(self, test_client, test_db, author_authenticated):
        """Test updating section with empty body returns 400"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/test-section-id",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400


class TestUpdateChapterNoData:
    """Tests for update chapter with no data - covers line 210"""

    def test_update_chapter_empty_body(self, test_client, test_db, author_authenticated):
        """Test updating chapter with empty body returns 400"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.put(
            f"/api/chapters/{chapter['id']}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "NO_UPDATE_DATA"


class TestSectionUpdateNotFoundCoverage:
    """Tests for section not found - covers line 596-599"""

    def test_update_section_not_found_returns_404(self, test_client, test_db, author_authenticated):
        """Test updating non-existent section returns 404"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/nonexistent-section-id",
            json={"title": "Updated Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestChapterGenerateViewerForbidden:
    """Test viewer forbidden for generate - covers 403 for generate"""

    def test_generate_chapter_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot generate chapter content"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.post(
            f"/api/chapters/{chapter['id']}/generate",
            json={"chapter_id": chapter["id"], "prompt": "Generate"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestSectionUpdateExpanded:
    """Expanded tests for section updates"""

    def test_update_section_with_title(self, test_client, test_db, author_authenticated):
        """Test updating section title"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/test-section-id",
            json={"title": "Updated Section Title"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Section Title"

    def test_update_section_with_order_num(self, test_client, test_db, author_authenticated):
        """Test updating section order"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/test-section-id",
            json={"order_num": 5},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_num"] == 5

    def test_update_section_with_status(self, test_client, test_db, author_authenticated):
        """Test updating section status"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/test-section-id",
            json={"status": "published"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"

    def test_update_section_with_multiple_fields(self, test_client, test_db, author_authenticated):
        """Test updating section with multiple fields"""
        token = author_authenticated["access_token"]
        user = author_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])
        create_test_section(test_db, chapter_id=chapter["id"], id="test-section-id")

        response = test_client.put(
            "/api/chapters/sections/test-section-id",
            json={
                "title": "Multi Field Section",
                "order_num": 3,
                "status": "reviewing",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Multi Field Section"
        assert data["order_num"] == 3
        assert data["status"] == "reviewing"


class TestChapterDeleteExpanded:
    """Expanded tests for chapter deletion"""

    def test_delete_chapter_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot delete chapters"""
        token = test_user_authenticated["access_token"]
        user = test_user_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.delete(
            f"/api/chapters/{chapter['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403

    def test_delete_chapter_content_admin(self, test_client, test_db, content_admin_authenticated):
        """Test content admin can delete any chapter"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        project = create_test_project(test_db, owner_id=user.id)
        chapter = create_test_chapter(test_db, project_id=project["id"])

        response = test_client.delete(
            f"/api/chapters/{chapter['id']}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
