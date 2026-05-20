"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # ─────────────────────────────────────────────────────────────────────────
    # 用户权限相关表
    # ─────────────────────────────────────────────────────────────────────────

    # 用户表
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='viewer'),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=True),
        sa.Column('clearance_level', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])

    # 角色表
    op.create_table(
        'roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # 权限表
    op.create_table(
        'permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.UniqueConstraint('resource', 'action', name='uq_permissions_resource_action'),
    )
    op.create_index('idx_permissions_resource_action', 'permissions', ['resource', 'action'])

    # 用户角色关联表
    op.create_table(
        'user_roles',
        sa.Column('user_id', UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', UUID(as_uuid=True),
                  sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )

    # 角色权限关联表
    op.create_table(
        'role_permissions',
        sa.Column('role_id', UUID(as_uuid=True),
                  sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', UUID(as_uuid=True),
                  sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 项目管理相关表
    # ─────────────────────────────────────────────────────────────────────────

    # 项目表
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('owner_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('total_chapters', sa.Integer(), server_default='0'),
        sa.Column('current_progress', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_owner', 'projects', ['owner_id'])

    # 项目成员表
    op.create_table(
        'project_members',
        sa.Column('project_id', UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # 章节表
    op.create_table(
        'chapters',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('order_num', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('parent_chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_chapters_project', 'chapters', ['project_id'])
    op.create_index('idx_chapters_status', 'chapters', ['status'])
    op.create_index('idx_chapters_parent', 'chapters', ['parent_chapter_id'])
    op.create_index('idx_chapters_order', 'chapters', ['project_id', 'order_num'])

    # 章节内容表
    op.create_table(
        'chapter_content',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_chapter_content_chapter', 'chapter_content', ['chapter_id'])
    op.create_index('idx_chapter_content_hash', 'chapter_content', ['content_hash'])

    # 小节表
    op.create_table(
        'sections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('order_num', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('parent_section_id', UUID(as_uuid=True),
                  sa.ForeignKey('sections.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_sections_chapter', 'sections', ['chapter_id'])
    op.create_index('idx_sections_parent', 'sections', ['parent_section_id'])
    op.create_index('idx_sections_order', 'sections', ['chapter_id', 'order_num'])

    # 概念表
    op.create_table(
        'concepts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('related_terms', ARRAY(sa.String()), nullable=True),
        sa.Column('source_chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id'), nullable=True),
        sa.Column('locked', sa.Boolean(), server_default='false'),
        sa.Column('properties', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_concepts_domain', 'concepts', ['domain'])
    op.create_index('idx_concepts_name', 'concepts', ['name'])
    op.create_index('idx_concepts_locked', 'concepts', ['locked'])

    # 术语表
    op.create_table(
        'terms',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('term', sa.String(200), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('synonyms', ARRAY(sa.String()), nullable=True),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('first_defined_at', sa.String(50), nullable=True),
        sa.Column('locked', sa.Boolean(), server_default='false'),
        sa.Column('properties', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_terms_domain', 'terms', ['domain'])
    op.create_index('idx_terms_term', 'terms', ['term'])
    op.create_index('idx_terms_locked', 'terms', ['locked'])

    # 审核记录表
    op.create_table(
        'reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_reviews_chapter', 'reviews', ['chapter_id'])
    op.create_index('idx_reviews_reviewer', 'reviews', ['reviewer_id'])
    op.create_index('idx_reviews_status', 'reviews', ['status'])

    # ─────────────────────────────────────────────────────────────────────────
    # 审计版本相关表
    # ─────────────────────────────────────────────────────────────────────────

    # 审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=True),
        sa.Column('result', sa.String(20), nullable=True),
        sa.Column('details', JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('signature', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_event_type', 'audit_logs', ['event_type'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])

    # 内容版本表
    op.create_table(
        'content_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('merkle_root', sa.String(128), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_content_versions_chapter', 'content_versions', ['chapter_id'])
    op.create_index('idx_content_versions_hash', 'content_versions', ['content_hash'])

    # ─────────────────────────────────────────────────────────────────────────
    # 素材引用相关表
    # ─────────────────────────────────────────────────────────────────────────

    # 素材资产表
    op.create_table(
        'material_assets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('copyright_info', sa.Text(), nullable=True),
        sa.Column('uploaded_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('properties', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_material_assets_hash', 'material_assets', ['file_hash'])
    op.create_index('idx_material_assets_uploader', 'material_assets', ['uploaded_by'])

    # 引用表
    op.create_table(
        'citations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', UUID(as_uuid=True),
                  sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doi', sa.String(255), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', ARRAY(sa.String()), nullable=True),
        sa.Column('journal', sa.String(255), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('verified', sa.Boolean(), server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('properties', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_citations_chapter', 'citations', ['chapter_id'])
    op.create_index('idx_citations_doi', 'citations', ['doi'])
    op.create_index('idx_citations_verified', 'citations', ['verified'])

    # ─────────────────────────────────────────────────────────────────────────
    # F32 知识图谱相关表
    # ─────────────────────────────────────────────────────────────────────────

    # 图谱节点表
    op.create_table(
        'graph_nodes',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('properties', JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_graph_nodes_type', 'graph_nodes', ['node_type'])
    op.create_index('idx_graph_nodes_properties', 'graph_nodes',
                    [op.text('properties')], postgresql_using='gin')

    # 图谱边表
    op.create_table(
        'graph_edges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_id', sa.String(255),
                  sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', sa.String(255),
                  sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('edge_type', sa.String(50), nullable=False),
        sa.Column('properties', JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_graph_edges_source', 'graph_edges', ['source_id'])
    op.create_index('idx_graph_edges_target', 'graph_edges', ['target_id'])
    op.create_index('idx_graph_edges_type', 'graph_edges', ['edge_type'])
    op.create_index('idx_graph_edges_source_target', 'graph_edges', ['source_id', 'target_id'])
    op.create_index('idx_graph_edges_properties', 'graph_edges',
                    [op.text('properties')], postgresql_using='gin')


def downgrade() -> None:
    op.drop_table('graph_edges')
    op.drop_table('graph_nodes')
    op.drop_table('citations')
    op.drop_table('material_assets')
    op.drop_table('content_versions')
    op.drop_table('audit_logs')
    op.drop_table('reviews')
    op.drop_table('terms')
    op.drop_table('concepts')
    op.drop_table('sections')
    op.drop_table('chapter_content')
    op.drop_table('chapters')
    op.drop_table('project_members')
    op.drop_table('projects')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
