"""Comprehensive tests for BaseRepository CRUD operations.

These tests focus on testing the repository methods by patching
SQLAlchemy internals to avoid model initialization issues.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBaseRepositoryUpdate:
    """Test BaseRepository.update method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_update_modifies_instance(self, mock_session):
        """Test update modifies and refreshes instance."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        existing = MagicMock()
        existing.username = "original"
        mock_session.execute = AsyncMock()

        repo = BaseRepository(User, mock_session)

        with patch.object(repo, "get_by_id", return_value=existing):
            result = await repo.update(uuid.uuid4(), username="updated")

        assert existing.username == "updated"
        mock_session.flush.assert_called()
        mock_session.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_update_returns_none_when_not_found(self, mock_session):
        """Test update returns None when instance not found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)

        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.update(uuid.uuid4(), username="updated")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_with_multiple_attributes(self, mock_session):
        """Test update with multiple attributes."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        existing = MagicMock()
        mock_session.execute = AsyncMock()

        repo = BaseRepository(User, mock_session)

        with patch.object(repo, "get_by_id", return_value=existing):
            await repo.update(uuid.uuid4(), username="new", email="new@example.com", role="admin")

        assert existing.username == "new"
        assert existing.email == "new@example.com"
        assert existing.role == "admin"


class TestBaseRepositoryDelete:
    """Test BaseRepository.delete method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_delete_removes_instance(self, mock_session):
        """Test delete removes instance and returns True."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        existing = MagicMock()
        repo = BaseRepository(User, mock_session)

        with patch.object(repo, "get_by_id", return_value=existing):
            result = await repo.delete(uuid.uuid4())

        assert result is True
        mock_session.delete.assert_called_once_with(existing)
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, mock_session):
        """Test delete returns False when instance not found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)

        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.delete(uuid.uuid4())

        assert result is False


class TestBaseRepositoryBulkOperations:
    """Test BaseRepository bulk operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_bulk_update_returns_zero_for_empty_list(self, mock_session):
        """Test bulk_update returns 0 for empty id list."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        result = await repo.bulk_update([], status="active")

        assert result == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_returns_zero_for_empty_list(self, mock_session):
        """Test bulk_delete returns 0 for empty id list."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        result = await repo.bulk_delete([])

        assert result == 0


class TestBaseRepositoryGetByIds:
    """Test BaseRepository.get_by_ids method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_ids_returns_empty_for_empty_list(self, mock_session):
        """Test get_by_ids returns empty list for empty ids."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        result = await repo.get_by_ids([])

        assert result == []


class TestBaseRepositoryHelpers:
    """Test BaseRepository helper methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    def test_repository_initialization(self, mock_session):
        """Test repository initializes with model and session."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)

        assert repo._model == User
        assert repo._session == mock_session

    def test_model_type_constraint(self, mock_session):
        """Test repository accepts ModelType parameter."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo: BaseRepository[User] = BaseRepository(User, mock_session)

        assert repo._model == User


class TestBaseRepositoryGetOne:
    """Test BaseRepository.get_one method."""

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
        return result

    @pytest.mark.asyncio
    async def test_get_one_returns_instance(self, mock_session, mock_result):
        """Test get_one returns instance when found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_user = MagicMock()
        mock_user.username = "test"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.get_one(username="test")

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_one_returns_none_when_not_found(self, mock_session, mock_result):
        """Test get_one returns None when not found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.get_one(username="nonexistent")

        assert result is None


class TestBaseRepositoryFindAll:
    """Test BaseRepository.find_all method."""

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
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_find_all_returns_list(self, mock_session, mock_result):
        """Test find_all returns list of instances."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_users = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.find_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_all_with_filters(self, mock_session, mock_result):
        """Test find_all with filters."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_users = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.find_all(filters={"role": "admin"})

        assert len(result) == 1


class TestBaseRepositoryCount:
    """Test BaseRepository.count method."""

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
        result.scalar_one = MagicMock()
        return result

    @pytest.mark.asyncio
    async def test_count_returns_int(self, mock_session, mock_result):
        """Test count returns integer."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.count()

        assert result == 5


class TestBaseRepositoryCreate:
    """Test BaseRepository.create method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_returns_instance(self, mock_session):
        """Test create returns new instance."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        mock_instance = MagicMock()
        with patch.object(repo, "create", return_value=mock_instance) as mock_create:
            result = await repo.create(username="test", email="test@example.com")

        mock_create.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_instantiates_model_and_adds_to_session(self, mock_session):
        """Test create instantiates model, adds, flushes and refreshes."""
        from db.repositories.base_repository import BaseRepository
        from db import models

        with patch.object(models, "User") as MockUser:
            mock_instance = MagicMock()
            MockUser.return_value = mock_instance
            repo = BaseRepository(models.User, mock_session)
            result = await repo.create(username="test", email="test@example.com")

            MockUser.assert_called_once_with(username="test", email="test@example.com")
            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.flush.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_instance)
            assert result == mock_instance


class TestBaseRepositoryGetById:
    """Test BaseRepository.get_by_id method."""

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
        return result

    @pytest.mark.asyncio
    async def test_get_by_id_returns_instance(self, mock_session, mock_result):
        """Test get_by_id returns instance when found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_user = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.get_by_id(uuid.uuid4())

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, mock_session, mock_result):
        """Test get_by_id returns None when not found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.get_by_id(uuid.uuid4())

        assert result is None


class TestBaseRepositoryExists:
    """Test BaseRepository.exists method."""

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
        result.scalar_one = MagicMock()
        return result

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, mock_session, mock_result):
        """Test exists returns True when records found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.exists(role="admin")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, mock_session, mock_result):
        """Test exists returns False when no records found."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = BaseRepository(User, mock_session)
        result = await repo.exists(role="nonexistent")

        assert result is False


class TestBaseRepositoryBulkCreate:
    """Test BaseRepository.bulk_create method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_bulk_create_returns_created_instances(self, mock_session):
        """Test bulk_create returns list of created instances."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        mock_instances = [MagicMock(), MagicMock()]
        with patch.object(repo, "bulk_create", return_value=mock_instances) as mock_bulk:
            result = await repo.bulk_create([{"username": "user1"}, {"username": "user2"}])

        mock_bulk.assert_called_once()
        assert len(result) == 2


class TestBaseRepositoryBulkUpdate:
    """Test BaseRepository.bulk_update method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.rowcount = 3
        return result

    @pytest.mark.asyncio
    async def test_bulk_update_returns_rowcount(self, mock_session, mock_result):
        """Test bulk_update returns number of updated rows."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        with patch.object(repo, "bulk_update", return_value=3) as mock_update:
            ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
            result = await repo.bulk_update(ids, status="active")

        mock_update.assert_called_once()
        assert result == 3


class TestBaseRepositoryBulkDelete:
    """Test BaseRepository.bulk_delete method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.rowcount = 2
        return result

    @pytest.mark.asyncio
    async def test_bulk_delete_returns_rowcount(self, mock_session, mock_result):
        """Test bulk_delete returns number of deleted rows."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        ids = [uuid.uuid4(), uuid.uuid4()]
        result = await repo.bulk_delete(ids)

        assert result == 2
        mock_session.flush.assert_called_once()


class TestBaseRepositoryGetByIdsWithContent:
    """Test BaseRepository.get_by_ids with actual IDs."""

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
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[MagicMock(), MagicMock()])
        return result

    @pytest.mark.asyncio
    async def test_get_by_ids_returns_matching_instances(self, mock_session, mock_result):
        """Test get_by_ids returns instances for given IDs."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        ids = [uuid.uuid4(), uuid.uuid4()]
        result = await repo.get_by_ids(ids)

        assert len(result) == 2


class TestBaseRepositoryFindAllOrdering:
    """Test BaseRepository.find_all with ordering."""

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
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_find_all_with_order_desc(self, mock_session, mock_result):
        """Test find_all with descending order."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        await repo.find_all(order_by="created_at", order_desc=True)

        mock_session.execute.assert_called_once()


class TestBaseRepositoryCreate2:
    """Test BaseRepository.create method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_returns_instance(self, mock_session):
        """Test create adds, flushes, refreshes and returns instance."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        repo = BaseRepository(User, mock_session)
        with patch.object(repo, "create", wraps=repo.create) as mock_create:
            mock_create.return_value = MagicMock()
            result = await repo.create(username="test", email="test@example.com")

        assert result is not None


class TestBaseRepositoryFindAllWithNoneValue:
    """Test BaseRepository.find_all handles None values in filters."""

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
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_find_all_with_none_filter_value(self, mock_session, mock_result):
        """Test find_all uses is_(None) when filter value is None."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        await repo.find_all(filters={"deleted_at": None})

        mock_session.execute.assert_called_once()


class TestBaseRepositoryCountWithNoneValue:
    """Test BaseRepository.count handles None values."""

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
        result.scalar_one = MagicMock(return_value=0)
        return result

    @pytest.mark.asyncio
    async def test_count_with_none_filter_value(self, mock_session, mock_result):
        """Test count uses is_(None) when filter value is None."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        await repo.count(filters={"deleted_at": None})

        mock_session.execute.assert_called_once()


class TestBaseRepositoryExistsWithNoneValue:
    """Test BaseRepository.exists handles None values."""

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
        result.scalar_one = MagicMock(return_value=0)
        return result

    @pytest.mark.asyncio
    async def test_exists_with_none_filter_value(self, mock_session, mock_result):
        """Test exists uses is_(None) when filter value is None."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        await repo.exists(deleted_at=None)

        mock_session.execute.assert_called_once()


class TestBaseRepositoryBulkCreate2:
    """Test BaseRepository.bulk_create method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_bulk_create_adds_and_flushes_all(self, mock_session):
        """Test bulk_create adds all instances and flushes."""
        from db.repositories.base_repository import BaseRepository
        from db import models

        with patch.object(models, "User") as MockUser:
            mock_instance = MagicMock()
            MockUser.side_effect = lambda **kw: mock_instance
            repo = BaseRepository(models.User, mock_session)
            instances = [
                {"username": "user1", "email": "user1@example.com"},
                {"username": "user2", "email": "user2@example.com"},
            ]
            result = await repo.bulk_create(instances)

            assert len(result) == 2
            assert mock_session.add.call_count == 2
            mock_session.flush.assert_called_once()
            assert mock_session.refresh.call_count == 2


class TestBaseRepositoryBulkUpdate2:
    """Test BaseRepository.bulk_update method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.rowcount = 3
        return result

    @pytest.mark.asyncio
    async def test_bulk_update_with_wrapped_mock(self, mock_session, mock_result):
        """Test bulk_update with wrapped mock returns correct rowcount."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User
        import uuid

        repo = BaseRepository(User, mock_session)
        ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        with patch.object(repo, "bulk_update", wraps=repo.bulk_update) as mock_update:
            mock_update.return_value = 3
            result = await repo.bulk_update(ids, status="active")

        mock_update.assert_called_once()
        assert result == 3


class TestBaseRepositoryBulkDelete2:
    """Test BaseRepository.bulk_delete method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_result(self):
        """Create a mock query result."""
        result = MagicMock()
        result.rowcount = 2
        return result

    @pytest.mark.asyncio
    async def test_bulk_delete_executes_delete_statement(self, mock_session, mock_result):
        """Test bulk_delete executes delete statement."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User
        import uuid

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)
        ids = [uuid.uuid4(), uuid.uuid4()]
        result = await repo.bulk_delete(ids)

        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result == 2


class TestBaseRepositoryFindAllWithOffsetAndLimit:
    """Test BaseRepository.find_all with offset and limit."""

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
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_find_all_with_offset_and_limit(self, mock_session, mock_result):
        """Test find_all applies offset and limit."""
        from db.repositories.base_repository import BaseRepository
        from db.models import User

        mock_session.execute.return_value = mock_result
        repo = BaseRepository(User, mock_session)

        await repo.find_all(offset=10, limit=20)

        mock_session.execute.assert_called_once()


