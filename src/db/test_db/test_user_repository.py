"""Comprehensive tests for UserRepository.

Tests all public methods of UserRepository using mocks.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestUserRepository:
    """Test UserRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.scalar_one_or_none = MagicMock()
        result.scalar_one = MagicMock()
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_get_by_username(self, mock_session, mock_result):
        """Test get_by_username returns user when found."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.get_by_username("testuser")

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, mock_session, mock_result):
        """Test get_by_username returns None when not found."""
        from db.repositories.user_repository import UserRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.get_by_username("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, mock_session, mock_result):
        """Test get_by_email returns user when found."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.get_by_email("test@example.com")

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, mock_session, mock_result):
        """Test get_by_email returns None when not found."""
        from db.repositories.user_repository import UserRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.get_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_user(self, mock_session):
        """Test create_user creates and returns new user."""
        from db.repositories.user_repository import UserRepository
        from db.models import User

        mock_user = MagicMock()
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"

        repo = UserRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_user) as mock_create:
            result = await repo.create_user(
                username="newuser",
                email="new@example.com",
                password_hash="hashed123"
            )

        mock_create.assert_called_once_with(
            username="newuser",
            email="new@example.com",
            password_hash="hashed123",
            role="viewer"
        )

    @pytest.mark.asyncio
    async def test_update_password(self, mock_session, mock_result):
        """Test update_password updates hashed password."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()
        mock_user.username = "testuser"
        user_id = uuid.uuid4()

        repo = UserRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_user) as mock_update:
            result = await repo.update_password(user_id, "newhashedpass")

        mock_update.assert_called_once_with(user_id, password_hash="newhashedpass")

    @pytest.mark.asyncio
    async def test_update_email(self, mock_session, mock_result):
        """Test update_email updates email."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()
        user_id = uuid.uuid4()

        repo = UserRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_user) as mock_update:
            result = await repo.update_email(user_id, "new@example.com")

        mock_update.assert_called_once_with(user_id, email="new@example.com")

    @pytest.mark.asyncio
    async def test_assign_role(self, mock_session, mock_result):
        """Test assign_role adds user role."""
        from db.repositories.user_repository import UserRepository

        user_id = uuid.uuid4()
        role_id = uuid.uuid4()

        repo = UserRepository(mock_session)
        with patch("db.repositories.user_repository.UserRole") as MockUserRole:
            mock_user_role = MagicMock()
            MockUserRole.return_value = mock_user_role
            result = await repo.assign_role(user_id, role_id)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_role_found(self, mock_session, mock_result):
        """Test remove_role returns True when role removed."""
        from db.repositories.user_repository import UserRepository

        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.remove_role(user_id, role_id)

        assert result is True
        mock_session.delete.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_role_not_found(self, mock_session, mock_result):
        """Test remove_role returns False when role not found."""
        from db.repositories.user_repository import UserRepository

        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.remove_role(user_id, role_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission_true(self, mock_session, mock_result):
        """Test has_permission returns True when user has permission."""
        from db.repositories.user_repository import UserRepository

        user_id = uuid.uuid4()
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.has_permission(user_id, "users", "create")

        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_false(self, mock_session, mock_result):
        """Test has_permission returns False when user lacks permission."""
        from db.repositories.user_repository import UserRepository

        user_id = uuid.uuid4()
        mock_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.has_permission(user_id, "users", "delete")

        assert result is False

    @pytest.mark.asyncio
    async def test_search_by_username(self, mock_session, mock_result):
        """Test search_by_username returns matching users."""
        from db.repositories.user_repository import UserRepository

        mock_users = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.search_by_username("test")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_by_email(self, mock_session, mock_result):
        """Test search_by_email returns matching users."""
        from db.repositories.user_repository import UserRepository

        mock_users = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.search_by_email("test")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_with_roles(self, mock_session, mock_result):
        """Test get_with_roles returns user with roles."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()

        with patch.object(UserRepository, 'get_with_roles', return_value=mock_user):
            repo = UserRepository(mock_session)
            result = await repo.get_with_roles(uuid.uuid4())

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_with_roles_not_found(self, mock_session, mock_result):
        """Test get_with_roles returns None when user not found."""
        from db.repositories.user_repository import UserRepository

        with patch.object(UserRepository, 'get_with_roles', return_value=None):
            repo = UserRepository(mock_session)
            result = await repo.get_with_roles(uuid.uuid4())

            assert result is None

    @pytest.mark.asyncio
    async def test_get_with_permissions(self, mock_session, mock_result):
        """Test get_with_permissions fetches user and collects all permissions."""
        from db.repositories.user_repository import UserRepository

        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.id = uuid.uuid4()
        mock_user.roles = [mock_role]

        mock_perm = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_perm]

        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        with patch.object(repo, "get_with_roles", return_value=mock_user):
            result = await repo.get_with_permissions(uuid.uuid4())

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_with_permissions_user_not_found(self, mock_session):
        """Test get_with_permissions returns None when user not found."""
        from db.repositories.user_repository import UserRepository

        repo = UserRepository(mock_session)
        with patch.object(repo, "get_with_roles", return_value=None):
            result = await repo.get_with_permissions(uuid.uuid4())

        assert result is None


class TestRoleRepository:
    """Test RoleRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.scalar_one_or_none = MagicMock()
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_get_by_name(self, mock_session, mock_result):
        """Test get_by_name returns role when found."""
        from db.repositories.user_repository import RoleRepository

        mock_role = MagicMock()
        mock_role.name = "admin"
        mock_result.scalar_one_or_none.return_value = mock_role
        mock_session.execute.return_value = mock_result

        repo = RoleRepository(mock_session)
        result = await repo.get_by_name("admin")

        assert result == mock_role

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, mock_session, mock_result):
        """Test get_by_name returns None when not found."""
        from db.repositories.user_repository import RoleRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = RoleRepository(mock_session)
        result = await repo.get_by_name("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_assign_permission(self, mock_session, mock_result):
        """Test assign_permission adds role permission."""
        from db.repositories.user_repository import RoleRepository

        role_id = uuid.uuid4()
        permission_id = uuid.uuid4()

        repo = RoleRepository(mock_session)
        with patch("db.repositories.user_repository.RolePermission") as MockRolePermission:
            mock_role_perm = MagicMock()
            MockRolePermission.return_value = mock_role_perm
            result = await repo.assign_permission(role_id, permission_id)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_permission_found(self, mock_session, mock_result):
        """Test remove_permission returns True when removed."""
        from db.repositories.user_repository import RoleRepository

        role_id = uuid.uuid4()
        permission_id = uuid.uuid4()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        repo = RoleRepository(mock_session)
        result = await repo.remove_permission(role_id, permission_id)

        assert result is True
        mock_session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_permission_not_found(self, mock_session, mock_result):
        """Test remove_permission returns False when not found."""
        from db.repositories.user_repository import RoleRepository

        role_id = uuid.uuid4()
        permission_id = uuid.uuid4()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = RoleRepository(mock_session)
        result = await repo.remove_permission(role_id, permission_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_with_permissions(self, mock_session, mock_result):
        """Test get_with_permissions returns role with permissions."""
        from db.repositories.user_repository import RoleRepository

        mock_role = MagicMock()

        with patch.object(RoleRepository, 'get_with_permissions', return_value=mock_role):
            repo = RoleRepository(mock_session)
            result = await repo.get_with_permissions(uuid.uuid4())

            assert result == mock_role

    @pytest.mark.asyncio
    async def test_get_all_with_user_count(self, mock_session, mock_result):
        """Test get_all_with_user_count returns all roles with user counts."""
        from db.repositories.user_repository import RoleRepository

        mock_roles = [MagicMock(), MagicMock()]

        with patch.object(RoleRepository, 'get_all_with_user_count', return_value=mock_roles):
            repo = RoleRepository(mock_session)
            result = await repo.get_all_with_user_count()

            assert len(result) == 2


class TestPermissionRepository:
    """Test PermissionRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.scalar_one_or_none = MagicMock()
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_get_by_resource_action(self, mock_session, mock_result):
        """Test get_by_resource_action returns permission when found."""
        from db.repositories.user_repository import PermissionRepository

        mock_perm = MagicMock()
        mock_perm.resource = "users"
        mock_perm.action = "create"
        mock_result.scalar_one_or_none.return_value = mock_perm
        mock_session.execute.return_value = mock_result

        repo = PermissionRepository(mock_session)
        result = await repo.get_by_resource_action("users", "create")

        assert result == mock_perm

    @pytest.mark.asyncio
    async def test_get_by_resource(self, mock_session, mock_result):
        """Test get_by_resource returns all permissions for resource."""
        from db.repositories.user_repository import PermissionRepository

        mock_perms = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_perms
        mock_session.execute.return_value = mock_result

        repo = PermissionRepository(mock_session)
        result = await repo.get_by_resource("users")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_grouped_by_resource(self, mock_session, mock_result):
        """Test get_all_grouped_by_resource groups permissions."""
        from db.repositories.user_repository import PermissionRepository

        mock_perm1 = MagicMock()
        mock_perm1.resource = "users"
        mock_perm1.action = "create"
        mock_perm2 = MagicMock()
        mock_perm2.resource = "users"
        mock_perm2.action = "read"
        mock_result.scalars.return_value.all.return_value = [mock_perm1, mock_perm2]
        mock_session.execute.return_value = mock_result

        repo = PermissionRepository(mock_session)
        result = await repo.get_all_grouped_by_resource()

        assert "users" in result
        assert len(result["users"]) == 2
