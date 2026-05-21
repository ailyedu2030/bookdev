"""seed data

Revision ID: 002_seed_data
Revises: 001_initial_schema
Create Date: 2025-01-01 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = '002_seed_data'
down_revision: str | None = '001_initial_schema'
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def generate_uuid() -> str:
    return 'gen_random_uuid()'


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # 插入默认角色
    # ─────────────────────────────────────────────────────────────────────────

    roles = [
        {
            'id': text(generate_uuid()),
            'name': 'admin',
            'description': '系统管理员，拥有所有权限',
        },
        {
            'id': text(generate_uuid()),
            'name': 'editor',
            'description': '编辑，可以创建和编辑内容',
        },
        {
            'id': text(generate_uuid()),
            'name': 'reviewer',
            'description': '审核员，可以审核内容',
        },
        {
            'id': text(generate_uuid()),
            'name': 'author',
            'description': '作者，可以创建和编辑自己的内容',
        },
        {
            'id': text(generate_uuid()),
            'name': 'viewer',
            'description': '查看者，只有查看权限',
        },
        {
            'id': text(generate_uuid()),
            'name': 'quality_manager',
            'description': '质量管理员，负责质量门禁管理',
        },
    ]

    for role in roles:
        op.execute(
            f"INSERT INTO roles (id, name, description) VALUES ('{role['id']}', '{role['name']}', '{role['description']}')"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 插入默认权限
    # ─────────────────────────────────────────────────────────────────────────

    permissions = [
        # 项目权限
        {'resource': 'project', 'action': 'create', 'description': '创建项目'},
        {'resource': 'project', 'action': 'read', 'description': '查看项目'},
        {'resource': 'project', 'action': 'update', 'description': '更新项目'},
        {'resource': 'project', 'action': 'delete', 'description': '删除项目'},
        {'resource': 'project', 'action': 'manage_members', 'description': '管理项目成员'},

        # 章节权限
        {'resource': 'chapter', 'action': 'create', 'description': '创建章节'},
        {'resource': 'chapter', 'action': 'read', 'description': '查看章节'},
        {'resource': 'chapter', 'action': 'update', 'description': '更新章节'},
        {'resource': 'chapter', 'action': 'delete', 'description': '删除章节'},
        {'resource': 'chapter', 'action': 'submit_review', 'description': '提交章节审核'},
        {'resource': 'chapter', 'action': 'approve', 'description': '批准章节'},
        {'resource': 'chapter', 'action': 'reject', 'description': '拒绝章节'},

        # 术语权限
        {'resource': 'term', 'action': 'create', 'description': '创建术语'},
        {'resource': 'term', 'action': 'read', 'description': '查看术语'},
        {'resource': 'term', 'action': 'update', 'description': '更新术语'},
        {'resource': 'term', 'action': 'delete', 'description': '删除术语'},
        {'resource': 'term', 'action': 'lock', 'description': '锁定术语'},

        # 概念权限
        {'resource': 'concept', 'action': 'create', 'description': '创建概念'},
        {'resource': 'concept', 'action': 'read', 'description': '查看概念'},
        {'resource': 'concept', 'action': 'update', 'description': '更新概念'},
        {'resource': 'concept', 'action': 'delete', 'description': '删除概念'},
        {'resource': 'concept', 'action': 'lock', 'description': '锁定概念'},

        # 素材权限
        {'resource': 'material', 'action': 'upload', 'description': '上传素材'},
        {'resource': 'material', 'action': 'read', 'description': '查看素材'},
        {'resource': 'material', 'action': 'delete', 'description': '删除素材'},

        # 用户管理权限
        {'resource': 'user', 'action': 'create', 'description': '创建用户'},
        {'resource': 'user', 'action': 'read', 'description': '查看用户'},
        {'resource': 'user', 'action': 'update', 'description': '更新用户'},
        {'resource': 'user', 'action': 'delete', 'description': '删除用户'},
        {'resource': 'user', 'action': 'assign_role', 'description': '分配角色'},

        # 知识图谱权限
        {'resource': 'knowledge_graph', 'action': 'read', 'description': '查看知识图谱'},
        {'resource': 'knowledge_graph', 'action': 'write', 'description': '修改知识图谱'},

        # 审计日志权限
        {'resource': 'audit_log', 'action': 'read', 'description': '查看审计日志'},

        # 质量门禁权限
        {'resource': 'quality_gate', 'action': 'manage', 'description': '管理质量门禁'},
        {'resource': 'quality_gate', 'action': 'bypass', 'description': '绕过质量门禁'},
    ]

    for perm in permissions:
        op.execute(
            f"INSERT INTO permissions (id, resource, action, description) VALUES "
            f"(gen_random_uuid(), '{perm['resource']}', '{perm['action']}', '{perm['description']}')"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 为管理员角色分配所有权限
    # ─────────────────────────────────────────────────────────────────────────

    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'admin'
        """
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 为编辑角色分配编辑相关权限
    # ─────────────────────────────────────────────────────────────────────────

    editor_permissions = [
        'project:read', 'project:update',
        'chapter:create', 'chapter:read', 'chapter:update',
        'term:create', 'term:read', 'term:update',
        'concept:create', 'concept:read', 'concept:update',
        'material:upload', 'material:read',
        'knowledge_graph:read', 'knowledge_graph:write',
    ]

    for perm in editor_permissions:
        resource, action = perm.split(':')
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'editor' AND p.resource = '{resource}' AND p.action = '{action}'
            """
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 为审核员角色分配审核相关权限
    # ─────────────────────────────────────────────────────────────────────────

    reviewer_permissions = [
        'chapter:read', 'chapter:submit_review', 'chapter:approve', 'chapter:reject',
        'term:read', 'concept:read',
        'knowledge_graph:read',
    ]

    for perm in reviewer_permissions:
        resource, action = perm.split(':')
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'reviewer' AND p.resource = '{resource}' AND p.action = '{action}'
            """
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 为作者角色分配作者相关权限
    # ─────────────────────────────────────────────────────────────────────────

    author_permissions = [
        'chapter:create', 'chapter:read', 'chapter:update', 'chapter:submit_review',
        'term:create', 'term:read', 'term:update',
        'concept:create', 'concept:read', 'concept:update',
        'material:upload', 'material:read',
        'knowledge_graph:read',
    ]

    for perm in author_permissions:
        resource, action = perm.split(':')
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'author' AND p.resource = '{resource}' AND p.action = '{action}'
            """
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 为查看者角色分配查看权限
    # ─────────────────────────────────────────────────────────────────────────

    viewer_permissions = [
        'project:read',
        'chapter:read',
        'term:read',
        'concept:read',
        'material:read',
        'knowledge_graph:read',
    ]

    for perm in viewer_permissions:
        resource, action = perm.split(':')
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'viewer' AND p.resource = '{resource}' AND p.action = '{action}'
            """
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 为质量管理员分配质量门禁权限
    # ─────────────────────────────────────────────────────────────────────────

    qm_permissions = [
        'quality_gate:manage', 'quality_gate:bypass',
        'chapter:read', 'chapter:approve', 'chapter:reject',
        'audit_log:read',
    ]

    for perm in qm_permissions:
        if ':' in perm:
            resource, action = perm.split(':')
            op.execute(
                f"""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r, permissions p
                WHERE r.name = 'quality_manager' AND p.resource = '{resource}' AND p.action = '{action}'
                """
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 创建默认管理员用户 (密码: admin123)
    # 密码哈希使用 bcrypt
    # ─────────────────────────────────────────────────────────────────────────

    # 注意：实际部署时应使用更安全的密码和密码哈希
    # bcrypt hash for 'admin123' with proper salt
    admin_password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.FQgM0l0s0z0XzK'

    op.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role, clearance_level)
        VALUES (
            gen_random_uuid(),
            'admin',
            'admin@example.com',
            '%s',
            'admin',
            3
        )
        """ % admin_password_hash
    )

    # 为管理员分配 admin 角色
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id
        FROM users u, roles r
        WHERE u.username = 'admin' AND r.name = 'admin'
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM user_roles WHERE user_id IN (SELECT id FROM users WHERE username = 'admin')")
    op.execute("DELETE FROM users WHERE username = 'admin'")
    op.execute("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE name IN ('admin', 'editor', 'reviewer', 'author', 'viewer', 'quality_manager'))")
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'editor', 'reviewer', 'author', 'viewer', 'quality_manager')")
    op.execute("DELETE FROM permissions")
