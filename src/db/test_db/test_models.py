"""Tests for SQLAlchemy models in db/models.

These tests verify model structure by importing classes and checking attributes
without triggering SQLAlchemy ORM initialization.
"""

import uuid


class TestModelImports:
    """Test that all models can be imported and have expected attributes."""

    def test_all_models_importable(self):
        """Verify all model classes can be imported from db.models."""
        from db.models import (
            AuditLog,
            Chapter,
            GraphEdge,
            GraphNode,
            Project,
            Role,
            User,
        )

        assert User is not None
        assert Role is not None
        assert Chapter is not None
        assert Project is not None
        assert AuditLog is not None
        assert GraphNode is not None
        assert GraphEdge is not None

    def test_user_model_tablename(self):
        """Verify User model has correct tablename."""
        from db.models import User

        assert User.__tablename__ == "users"
        assert hasattr(User, "id")
        assert hasattr(User, "username")
        assert hasattr(User, "email")
        assert hasattr(User, "password_hash")
        assert hasattr(User, "role")

    def test_role_model_tablename(self):
        """Verify Role model has correct tablename."""
        from db.models import Role

        assert Role.__tablename__ == "roles"
        assert hasattr(Role, "id")
        assert hasattr(Role, "name")

    def test_chapter_model_tablename(self):
        """Verify Chapter model has correct tablename."""
        from db.models import Chapter

        assert Chapter.__tablename__ == "chapters"
        assert hasattr(Chapter, "id")
        assert hasattr(Chapter, "project_id")
        assert hasattr(Chapter, "title")
        assert hasattr(Chapter, "order_num")
        assert hasattr(Chapter, "status")

    def test_project_model_tablename(self):
        """Verify Project model has correct tablename."""
        from db.models import Project

        assert Project.__tablename__ == "projects"
        assert hasattr(Project, "id")
        assert hasattr(Project, "name")
        assert hasattr(Project, "owner_id")
        assert hasattr(Project, "status")

    def test_graph_node_model_tablename(self):
        """Verify GraphNode model has correct tablename."""
        from db.models import GraphNode

        assert GraphNode.__tablename__ == "graph_nodes"
        assert hasattr(GraphNode, "id")
        assert hasattr(GraphNode, "node_type")
        assert hasattr(GraphNode, "properties")

    def test_graph_edge_model_tablename(self):
        """Verify GraphEdge model has correct tablename."""
        from db.models import GraphEdge

        assert GraphEdge.__tablename__ == "graph_edges"
        assert hasattr(GraphEdge, "id")
        assert hasattr(GraphEdge, "source_id")
        assert hasattr(GraphEdge, "target_id")
        assert hasattr(GraphEdge, "edge_type")

    def test_term_model_tablename(self):
        """Verify Term model has correct tablename."""
        from db.models import Term

        assert Term.__tablename__ == "terms"
        assert hasattr(Term, "id")
        assert hasattr(Term, "term")
        assert hasattr(Term, "definition")
        assert hasattr(Term, "domain")

    def test_audit_log_model_tablename(self):
        """Verify AuditLog model has correct tablename."""
        from db.models import AuditLog

        assert AuditLog.__tablename__ == "audit_logs"
        assert hasattr(AuditLog, "id")
        assert hasattr(AuditLog, "event_type")
        assert hasattr(AuditLog, "action")

    def test_chapter_content_model_tablename(self):
        """Verify ChapterContent model has correct tablename."""
        from db.models import ChapterContent

        assert ChapterContent.__tablename__ == "chapter_content"
        assert hasattr(ChapterContent, "id")
        assert hasattr(ChapterContent, "chapter_id")
        assert hasattr(ChapterContent, "content")

    def test_section_model_tablename(self):
        """Verify Section model has correct tablename."""
        from db.models import Section

        assert Section.__tablename__ == "sections"
        assert hasattr(Section, "id")
        assert hasattr(Section, "chapter_id")
        assert hasattr(Section, "title")
        assert hasattr(Section, "order_num")

    def test_concept_model_tablename(self):
        """Verify Concept model has correct tablename."""
        from db.models import Concept

        assert Concept.__tablename__ == "concepts"
        assert hasattr(Concept, "id")
        assert hasattr(Concept, "name")
        assert hasattr(Concept, "definition")

    def test_project_member_model_tablename(self):
        """Verify ProjectMember model has correct tablename."""
        from db.models import ProjectMember

        assert ProjectMember.__tablename__ == "project_members"
        assert hasattr(ProjectMember, "project_id")
        assert hasattr(ProjectMember, "user_id")
        assert hasattr(ProjectMember, "role")

    def test_review_model_tablename(self):
        """Verify Review model has correct tablename."""
        from db.models import Review

        assert Review.__tablename__ == "reviews"
        assert hasattr(Review, "id")
        assert hasattr(Review, "chapter_id")
        assert hasattr(Review, "reviewer_id")

    def test_content_version_model_tablename(self):
        """Verify ContentVersion model has correct tablename."""
        from db.models import ContentVersion

        assert ContentVersion.__tablename__ == "content_versions"
        assert hasattr(ContentVersion, "id")
        assert hasattr(ContentVersion, "chapter_id")

    def test_material_asset_model_tablename(self):
        """Verify MaterialAsset model has correct tablename."""
        from db.models import MaterialAsset

        assert MaterialAsset.__tablename__ == "material_assets"
        assert hasattr(MaterialAsset, "id")
        assert hasattr(MaterialAsset, "filename")
        assert hasattr(MaterialAsset, "file_hash")

    def test_citation_model_tablename(self):
        """Verify Citation model has correct tablename."""
        from db.models import Citation

        assert Citation.__tablename__ == "citations"
        assert hasattr(Citation, "id")
        assert hasattr(Citation, "chapter_id")

    def test_permission_model_tablename(self):
        """Verify Permission model has correct tablename."""
        from db.models import Permission

        assert Permission.__tablename__ == "permissions"
        assert hasattr(Permission, "id")
        assert hasattr(Permission, "resource")
        assert hasattr(Permission, "action")

    def test_user_role_model_tablename(self):
        """Verify UserRole model has correct tablename."""
        from db.models import UserRole

        assert UserRole.__tablename__ == "user_roles"
        assert hasattr(UserRole, "user_id")
        assert hasattr(UserRole, "role_id")

    def test_role_permission_model_tablename(self):
        """Verify RolePermission model has correct tablename."""
        from db.models import RolePermission

        assert RolePermission.__tablename__ == "role_permissions"
        assert hasattr(RolePermission, "role_id")
        assert hasattr(RolePermission, "permission_id")

    def test_generate_uuid_function(self):
        """Verify generate_uuid produces valid UUIDs."""
        from db.models import generate_uuid

        uid = generate_uuid()
        assert isinstance(uid, uuid.UUID)
        assert uid != uuid.UUID(int=0)

    def test_base_model_has_no_tablename_on_base_class(self):
        """Verify Base model does not define a tablename (only subclasses do)."""
        from db import Base

        assert not hasattr(Base, "__tablename__") or Base.__tablename__ is None


class TestDbModuleExports:
    """Test db module exports."""

    def test_base_exported(self):
        """Verify Base is exported from db."""
        from db import Base

        assert Base is not None

    def test_async_session_exported(self):
        """Verify AsyncSession is used in db module."""
        from db import get_db_session, get_session

        assert callable(get_session)
        assert callable(get_db_session)

    def test_db_module_all(self):
        """Verify db module __all__ contains expected items."""
        from db import __all__

        assert "Base" in __all__
        assert "get_session" in __all__
        assert "get_db_session" in __all__
