"""
Unit Tests for API Schemas

Tests for schema validation:
- Auth schemas (UserCreate, UserLogin, Token, etc.)
- Common schemas (PaginatedResponse, ErrorResponse, etc.)
- Project schemas
- Chapter schemas
- Term schemas
"""


import pytest
from api.schemas.auth import (
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    PermissionResponse,
    RefreshTokenRequest,
    RoleResponse,
    Token,
    TokenPayload,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from api.schemas.chapter import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    ContentVersionResponse,
    ReviewApprove,
    ReviewReject,
    ReviewResponse,
    ReviewSubmit,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from api.schemas.common import (
    ChapterIDParams,
    DOIVerifyRequest,
    DOIVerifyResponse,
    ErrorResponse,
    HealthResponse,
    IDParams,
    LogEntry,
    MetricsResponse,
    PaginatedResponse,
    PaginationParams,
    ProjectIDParams,
    RegulationVerifyRequest,
    RegulationVerifyResponse,
    ScanRequest,
    ScanResponse,
    SemanticScanRequest,
    SemanticScanResponse,
    SuccessResponse,
)
from api.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
)
from api.schemas.term import (
    CitationCreate,
    CitationResponse,
    ConceptCreate,
    ConceptResponse,
    ConceptUpdate,
    TermCreate,
    TermLockRequest,
    TermResponse,
    TermSearchRequest,
    TermUpdate,
)
from pydantic import ValidationError


class TestAuthSchemas:
    """Tests for authentication schemas"""

    def test_user_create_valid(self):
        """Test valid UserCreate schema"""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="securepassword123",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "securepassword123"
        assert user.role == "viewer"

    def test_user_create_with_role(self):
        """Test UserCreate with custom role"""
        user = UserCreate(
            username="admin",
            email="admin@example.com",
            password="password123",
            role="system_admin",
        )
        assert user.role == "system_admin"

    def test_user_create_with_organization(self):
        """Test UserCreate with organization"""
        user = UserCreate(
            username="orguser",
            email="org@example.com",
            password="password123",
            organization_id="org-123",
        )
        assert user.organization_id == "org-123"

    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="securepassword123",
            )

    def test_user_create_short_password(self):
        """Test UserCreate with short password"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short",
            )

    def test_user_create_long_password(self):
        """Test UserCreate with password exceeding max length"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="a" * 129,
            )

    def test_user_create_short_username(self):
        """Test UserCreate with short username"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",
                email="test@example.com",
                password="securepassword123",
            )

    def test_user_create_long_username(self):
        """Test UserCreate with username exceeding max length"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="a" * 101,
                email="test@example.com",
                password="securepassword123",
            )

    def test_user_login_valid(self):
        """Test valid UserLogin schema"""
        login = UserLogin(
            email="test@example.com",
            password="password123",
        )
        assert login.email == "test@example.com"
        assert login.password == "password123"

    def test_user_login_invalid_email(self):
        """Test UserLogin with invalid email"""
        with pytest.raises(ValidationError):
            UserLogin(
                email="not-an-email",
                password="password123",
            )

    def test_user_response_valid(self):
        """Test valid UserResponse schema"""
        response = UserResponse(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="viewer",
            organization_id="org-123",
            clearance_level=1,
            created_at="2025-01-01T00:00:00",
        )
        assert response.id == "user-123"
        assert response.username == "testuser"
        assert response.clearance_level == 1

    def test_user_update_partial(self):
        """Test UserUpdate with partial data"""
        update = UserUpdate(username="newusername")
        assert update.username == "newusername"
        assert update.email is None

    def test_user_update_invalid_email(self):
        """Test UserUpdate with invalid email"""
        with pytest.raises(ValidationError):
            UserUpdate(email="not-an-email")

    def test_user_update_invalid_clearance(self):
        """Test UserUpdate with out-of-range clearance level"""
        with pytest.raises(ValidationError):
            UserUpdate(clearance_level=10)

    def test_user_role_update_valid(self):
        """Test valid UserRoleUpdate schema"""
        update = UserRoleUpdate(role="editor")
        assert update.role == "editor"

    def test_user_role_update_invalid_role(self):
        """Test UserRoleUpdate with invalid role"""
        with pytest.raises(ValidationError):
            UserRoleUpdate(role="invalid_role")

    def test_token_valid(self):
        """Test valid Token schema"""
        token = Token(
            access_token="access123",
            refresh_token="refresh456",
        )
        assert token.access_token == "access123"
        assert token.refresh_token == "refresh456"
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_token_payload_valid(self):
        """Test valid TokenPayload schema"""
        payload = TokenPayload(
            sub="user-123",
            email="test@example.com",
            role="viewer",
            exp=1234567890,
            iat=1234567800,
            type="access",
        )
        assert payload.sub == "user-123"
        assert payload.type == "access"

    def test_refresh_token_request_valid(self):
        """Test valid RefreshTokenRequest schema"""
        request = RefreshTokenRequest(refresh_token="token123")
        assert request.refresh_token == "token123"

    def test_password_change_valid(self):
        """Test valid PasswordChange schema"""
        change = PasswordChange(
            old_password="oldpass123",
            new_password="newpass456",
        )
        assert change.old_password == "oldpass123"
        assert change.new_password == "newpass456"

    def test_password_change_short_new_password(self):
        """Test PasswordChange with short new password"""
        with pytest.raises(ValidationError):
            PasswordChange(
                old_password="oldpass123",
                new_password="short",
            )

    def test_password_reset_request_valid(self):
        """Test valid PasswordResetRequest schema"""
        request = PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"

    def test_password_reset_confirm_valid(self):
        """Test valid PasswordResetConfirm schema"""
        confirm = PasswordResetConfirm(
            token="reset-token",
            new_password="newpassword123",
        )
        assert confirm.token == "reset-token"
        assert confirm.new_password == "newpassword123"

    def test_role_response_valid(self):
        """Test valid RoleResponse schema"""
        response = RoleResponse(
            id="role-123",
            name="Editor",
            description="Can edit content",
            created_at="2025-01-01T00:00:00",
        )
        assert response.name == "Editor"

    def test_permission_response_valid(self):
        """Test valid PermissionResponse schema"""
        response = PermissionResponse(
            id="perm-123",
            resource="projects",
            action="create",
            description="Can create projects",
        )
        assert response.resource == "projects"
        assert response.action == "create"


class TestCommonSchemas:
    """Tests for common schemas"""

    def test_paginated_response_valid(self):
        """Test valid PaginatedResponse schema"""
        response = PaginatedResponse(
            data=[{"id": "1"}, {"id": "2"}],
            meta={"total": 2, "page": 1, "per_page": 20, "total_pages": 1},
        )
        assert len(response.data) == 2
        assert response.success is True

    def test_paginated_response_defaults(self):
        """Test PaginatedResponse default values"""
        response = PaginatedResponse(data=[])
        assert response.success is True
        assert response.meta["total"] == 0
        assert response.meta["page"] == 1

    def test_error_response_valid(self):
        """Test valid ErrorResponse schema"""
        response = ErrorResponse(
            error={"code": "NOT_FOUND", "message": "Resource not found"}
        )
        assert response.success is False
        assert response.error.code == "NOT_FOUND"

    def test_error_response_defaults(self):
        """Test ErrorResponse default values"""
        response = ErrorResponse()
        assert response.success is False
        assert response.error.code == "INTERNAL_ERROR"

    def test_success_response_valid(self):
        """Test valid SuccessResponse schema"""
        response = SuccessResponse(
            message="Operation completed",
            data={"id": "123"},
        )
        assert response.success is True
        assert response.message == "Operation completed"

    def test_health_response_valid(self):
        """Test valid HealthResponse schema"""
        response = HealthResponse(
            status="healthy",
            components={"database": "up", "cache": "up"},
        )
        assert response.status == "healthy"
        assert response.components is not None
        assert response.components.get("database") == "up"

    def test_health_response_defaults(self):
        """Test HealthResponse default values"""
        response = HealthResponse(status="healthy")
        assert response.version == "1.0.0"

    def test_metrics_response_valid(self):
        """Test valid MetricsResponse schema"""
        response = MetricsResponse(
            data={"requests": 1000, "errors": 5},
        )
        assert response.success is True
        assert response.data["requests"] == 1000

    def test_log_entry_valid(self):
        """Test valid LogEntry schema"""
        entry = LogEntry(
            id="log-123",
            event_type="user_login",
            user_id="user-456",
            action="login",
            result="success",
            created_at="2025-01-01T00:00:00",
        )
        assert entry.event_type == "user_login"
        assert entry.result == "success"

    def test_pagination_params_defaults(self):
        """Test PaginationParams default values"""
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 20
        assert params.sort_order == "desc"

    def test_pagination_params_invalid_page(self):
        """Test PaginationParams with invalid page"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_pagination_params_invalid_per_page(self):
        """Test PaginationParams with per_page out of range"""
        with pytest.raises(ValidationError):
            PaginationParams(per_page=101)

    def test_pagination_params_invalid_sort_order(self):
        """Test PaginationParams with invalid sort order"""
        with pytest.raises(ValidationError):
            PaginationParams(sort_order="invalid")

    def test_id_params_valid(self):
        """Test valid IDParams schema"""
        params = IDParams(id="entity-123")
        assert params.id == "entity-123"

    def test_project_id_params_valid(self):
        """Test valid ProjectIDParams schema"""
        params = ProjectIDParams(project_id="project-123")
        assert params.project_id == "project-123"

    def test_chapter_id_params_valid(self):
        """Test valid ChapterIDParams schema"""
        params = ChapterIDParams(id="chapter-123")
        assert params.id == "chapter-123"

    def test_scan_request_valid(self):
        """Test valid ScanRequest schema"""
        request = ScanRequest(
            content="This is content to scan",
            categories=["spam", "violence"],
        )
        assert request.content == "This is content to scan"
        assert request.categories is not None and len(request.categories) == 2

    def test_scan_response_valid(self):
        """Test valid ScanResponse schema"""
        response = ScanResponse(
            is_safe=True,
            confidence_score=0.95,
            categories=[],
            violations=[],
            action="allow",
            details="Content is safe",
        )
        assert response.is_safe is True
        assert response.confidence_score == 0.95

    def test_doi_verify_request_valid(self):
        """Test valid DOIVerifyRequest schema"""
        request = DOIVerifyRequest(doi="10.1234/example")
        assert request.doi == "10.1234/example"

    def test_doi_verify_response_valid(self):
        """Test valid DOIVerifyResponse schema"""
        response = DOIVerifyResponse(
            valid=True,
            doi="10.1234/example",
            metadata={"title": "Test Paper"},
        )
        assert response.valid is True
        assert response.metadata is not None and response.metadata["title"] == "Test Paper"

    def test_regulation_verify_request_valid(self):
        """Test valid RegulationVerifyRequest schema"""
        request = RegulationVerifyRequest(
            content="Content to verify",
            law_type="copyright",
        )
        assert request.law_type == "copyright"

    def test_regulation_verify_response_valid(self):
        """Test valid RegulationVerifyResponse schema"""
        response = RegulationVerifyResponse(
            valid=True,
            matched_laws=[{"name": "Copyright Act"}],
            confidence=0.9,
            details="No violations found",
        )
        assert response.valid is True
        assert response.confidence == 0.9

    def test_semantic_scan_request_valid(self):
        """Test valid SemanticScanRequest schema"""
        request = SemanticScanRequest(
            content="Content to scan",
            threshold=0.8,
        )
        assert request.threshold == 0.8

    def test_semantic_scan_request_threshold_bounds(self):
        """Test SemanticScanRequest threshold bounds"""
        with pytest.raises(ValidationError):
            SemanticScanRequest(content="test", threshold=1.5)
        with pytest.raises(ValidationError):
            SemanticScanRequest(content="test", threshold=-0.1)

    def test_semantic_scan_response_valid(self):
        """Test valid SemanticScanResponse schema"""
        response = SemanticScanResponse(
            issues=[],
            score=0.9,
            summary="Content is consistent",
        )
        assert response.score == 0.9


class TestProjectSchemas:
    """Tests for project schemas"""

    def test_project_create_valid(self):
        """Test valid ProjectCreate schema"""
        project = ProjectCreate(
            name="Test Project",
            description="A test project description",
        )
        assert project.name == "Test Project"

    def test_project_create_minimal(self):
        """Test minimal ProjectCreate schema"""
        project = ProjectCreate(name="Minimal Project")
        assert project.name == "Minimal Project"

    def test_project_create_empty_name(self):
        """Test ProjectCreate with empty name"""
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_project_update_valid(self):
        """Test valid ProjectUpdate schema"""
        update = ProjectUpdate(
            name="Updated Name",
            description="Updated description",
        )
        assert update.name == "Updated Name"

    def test_project_update_partial(self):
        """Test partial ProjectUpdate"""
        update = ProjectUpdate(status="active")
        assert update.status == "active"
        assert update.name is None

    def test_project_update_invalid_status(self):
        """Test ProjectUpdate with invalid status"""
        with pytest.raises(ValidationError):
            ProjectUpdate(status="invalid_status")

    def test_project_response_valid(self):
        """Test valid ProjectResponse schema"""
        response = ProjectResponse(
            id="proj-123",
            name="Test Project",
            description="Description",
            status="draft",
            owner_id="user-123",
            total_chapters=5,
            current_progress=0,
            created_at="2025-01-01T00:00:00",
        )
        assert response.id == "proj-123"
        assert response.total_chapters == 5

    def test_project_member_add_valid(self):
        """Test valid ProjectMemberAdd schema"""
        member = ProjectMemberAdd(
            user_id="user-123",
            role="editor",
        )
        assert member.user_id == "user-123"
        assert member.role == "editor"

    def test_project_member_add_invalid_role(self):
        """Test ProjectMemberAdd with invalid role"""
        with pytest.raises(ValidationError):
            ProjectMemberAdd(
                user_id="user-123",
                role="admin",
            )

    def test_project_stats_valid(self):
        """Test valid ProjectStats schema"""
        stats = ProjectStats(
            total_chapters=10,
            completed_chapters=3,
            in_progress_chapters=2,
            draft_chapters=5,
            total_words=50000,
            reviewed_chapters=1,
            approved_chapters=2,
        )
        assert stats.total_chapters == 10
        assert stats.completed_chapters == 3


class TestChapterSchemas:
    """Tests for chapter schemas"""

    def test_chapter_create_valid(self):
        """Test valid ChapterCreate schema"""
        chapter = ChapterCreate(
            project_id="proj-123",
            title="Chapter 1",
            order_num=1,
        )
        assert chapter.title == "Chapter 1"
        assert chapter.order_num == 1

    def test_chapter_create_with_parent(self):
        """Test ChapterCreate with parent chapter"""
        chapter = ChapterCreate(
            project_id="proj-123",
            title="Subchapter 1.1",
            order_num=1,
            parent_chapter_id="chapter-parent-123",
        )
        assert chapter.parent_chapter_id == "chapter-parent-123"

    def test_chapter_create_empty_title(self):
        """Test ChapterCreate with empty title"""
        with pytest.raises(ValidationError):
            ChapterCreate(
                project_id="proj-123",
                title="",
                order_num=1,
            )

    def test_chapter_update_valid(self):
        """Test valid ChapterUpdate schema"""
        update = ChapterUpdate(
            title="Updated Title",
            content="Updated content...",
            status="reviewing",
        )
        assert update.title == "Updated Title"

    def test_chapter_update_invalid_status(self):
        """Test ChapterUpdate with invalid status"""
        with pytest.raises(ValidationError):
            ChapterUpdate(status="invalid_status")

    def test_chapter_response_valid(self):
        """Test valid ChapterResponse schema"""
        response = ChapterResponse(
            id="chapter-123",
            project_id="proj-123",
            title="Chapter 1",
            order_num=1,
            status="draft",
            word_count=1000,
            version="1.0",
            created_at="2025-01-01T00:00:00",
        )
        assert response.word_count == 1000

    def test_review_submit_valid(self):
        """Test valid ReviewSubmit schema"""
        submit = ReviewSubmit(
            chapter_id="chapter-123",
            comments="Ready for review",
        )
        assert submit.comments == "Ready for review"

    def test_review_approve_valid(self):
        """Test valid ReviewApprove schema"""
        approve = ReviewApprove(
            chapter_id="chapter-123",
            comments="Approved",
        )
        assert approve.chapter_id == "chapter-123"

    def test_review_reject_valid(self):
        """Test valid ReviewReject schema"""
        reject = ReviewReject(
            chapter_id="chapter-123",
            comments="Needs revision",
        )
        assert reject.comments == "Needs revision"

    def test_review_reject_requires_comments(self):
        """Test ReviewReject requires non-empty comments"""
        with pytest.raises(ValidationError):
            ReviewReject(
                chapter_id="chapter-123",
                comments="",
            )

    def test_review_response_valid(self):
        """Test valid ReviewResponse schema"""
        response = ReviewResponse(
            id="review-123",
            chapter_id="chapter-123",
            status="approved",
            reviewer_id="reviewer-123",
            comments="Looks good",
            reviewed_at="2025-01-01T00:00:00",
        )
        assert response.status == "approved"

    def test_section_create_valid(self):
        """Test valid SectionCreate schema"""
        section = SectionCreate(
            chapter_id="chapter-123",
            title="Section 1",
            order_num=1,
        )
        assert section.title == "Section 1"

    def test_section_create_with_parent(self):
        """Test SectionCreate with parent section"""
        section = SectionCreate(
            chapter_id="chapter-123",
            title="Subsection 1.1",
            order_num=1,
            parent_section_id="section-parent-123",
        )
        assert section.parent_section_id == "section-parent-123"

    def test_section_update_valid(self):
        """Test valid SectionUpdate schema"""
        update = SectionUpdate(
            title="Updated Section",
            content="Updated content...",
        )
        assert update.title == "Updated Section"

    def test_section_response_valid(self):
        """Test valid SectionResponse schema"""
        response = SectionResponse(
            id="section-123",
            chapter_id="chapter-123",
            title="Section 1",
            order_num=1,
            status="draft",
            created_at="2025-01-01T00:00:00",
        )
        assert response.order_num == 1

    def test_content_version_response_valid(self):
        """Test valid ContentVersionResponse schema"""
        response = ContentVersionResponse(
            id="version-123",
            chapter_id="chapter-123",
            version="2.0",
            content_hash="abc123",
            created_at="2025-01-01T00:00:00",
        )
        assert response.version == "2.0"


class TestTermSchemas:
    """Tests for term schemas"""

    def test_term_create_valid(self):
        """Test valid TermCreate schema"""
        term = TermCreate(
            term="Blockchain",
            definition="A distributed ledger technology",
            domain="technology",
            synonyms=["distributed ledger"],
        )
        assert term.term == "Blockchain"
        assert term.domain == "technology"

    def test_term_create_empty_term(self):
        """Test TermCreate with empty term"""
        with pytest.raises(ValidationError):
            TermCreate(
                term="",
                definition="A definition",
            )

    def test_term_create_empty_definition(self):
        """Test TermCreate with empty definition"""
        with pytest.raises(ValidationError):
            TermCreate(
                term="Valid Term",
                definition="",
            )

    def test_term_update_valid(self):
        """Test valid TermUpdate schema"""
        update = TermUpdate(
            definition="Updated definition",
            domain="new_domain",
        )
        assert update.definition == "Updated definition"

    def test_term_response_valid(self):
        """Test valid TermResponse schema"""
        response = TermResponse(
            id="term-123",
            term="AI",
            definition="Artificial Intelligence",
            domain="technology",
            synonyms=["Machine Learning"],
            locked=False,
            version=1,
            created_at="2025-01-01T00:00:00",
        )
        assert response.locked is False

    def test_term_lock_request_valid(self):
        """Test valid TermLockRequest schema"""
        lock = TermLockRequest(
            reason="Pending review",
        )
        assert lock.reason == "Pending review"

    def test_term_search_request_valid(self):
        """Test valid TermSearchRequest schema"""
        request = TermSearchRequest(
            query="blockchain",
            domain="technology",
            limit=10,
        )
        assert request.query == "blockchain"
        assert request.limit == 10

    def test_term_search_request_defaults(self):
        """Test TermSearchRequest default values"""
        request = TermSearchRequest(query="test")
        assert request.domain is None
        assert request.limit == 10

    def test_concept_create_valid(self):
        """Test valid ConceptCreate schema"""
        concept = ConceptCreate(
            name="Deep Learning",
            definition="A subset of machine learning",
            domain="AI",
            related_terms=["Neural Network", "AI"],
        )
        assert concept.name == "Deep Learning"

    def test_concept_update_valid(self):
        """Test valid ConceptUpdate schema"""
        update = ConceptUpdate(
            definition="Updated definition",
            locked=True,
        )
        assert update.definition == "Updated definition"
        assert update.locked is True

    def test_concept_response_valid(self):
        """Test valid ConceptResponse schema"""
        response = ConceptResponse(
            id="concept-123",
            name="Machine Learning",
            definition="Learning from data",
            created_at="2025-01-01T00:00:00",
        )
        assert response.locked is False

    def test_citation_create_valid(self):
        """Test valid CitationCreate schema"""
        citation = CitationCreate(
            chapter_id="chapter-123",
            doi="10.1234/example",
            title="Example Paper",
            authors=["John Doe", "Jane Smith"],
            journal="Nature",
            year=2024,
        )
        assert citation.title == "Example Paper"
        assert citation.year == 2024

    def test_citation_create_minimal(self):
        """Test minimal CitationCreate schema"""
        citation = CitationCreate(
            chapter_id="chapter-123",
            title="Minimal Citation",
        )
        assert citation.title == "Minimal Citation"

    def test_citation_response_valid(self):
        """Test valid CitationResponse schema"""
        response = CitationResponse(
            id="citation-123",
            chapter_id="chapter-123",
            title="Example Paper",
            verified=True,
            created_at="2025-01-01T00:00:00",
        )
        assert response.verified is True
