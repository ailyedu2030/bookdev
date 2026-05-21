"""
Repository 模块单元测试

使用 mock 模拟数据库操作，为 db/repositories 模块提供单元测试覆盖。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from db.repositories.audit_log_repository import AuditLogRepository
from db.repositories.base_repository import BaseRepository
from db.repositories.chapter_repository import (
    ChapterContentRepository,
    ChapterRepository,
    SectionRepository,
)
from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from db.repositories.project_repository import (
    ProjectMemberRepository,
    ProjectRepository,
)
from db.repositories.term_repository import ConceptRepository, TermRepository
from db.repositories.user_repository import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
)


class MockAsyncSession:
    """模拟 AsyncSession"""
    def __init__(self):
        self.add = MagicMock()
        self._flush_mock = AsyncMock()
        self.refresh = AsyncMock()
        self._delete_mock = AsyncMock()
        self.execute = AsyncMock()
        self._begin_mock = AsyncMock()

    async def delete(self, instance):
        await self._delete_mock(instance)

    async def flush(self):
        await self._flush_mock()

    def begin(self):
        """Return an async context manager for transactions"""
        return self._begin_mock


class MockSelectResult:
    def __init__(self, scalar_value=None, scalars_value=None):
        self._scalar_value = scalar_value
        self._scalars_value = scalars_value or []

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalar_one(self):
        return self._scalar_value

    def scalars(self):
        return self

    def all(self):
        return self._scalars_value


class MockExecuteResult:
    def __init__(self, scalar_value=None, scalars_value=None, rowcount=0, fetch_result=None):
        self._scalar_value = scalar_value
        self._scalars_value = scalars_value or []
        self._rowcount = rowcount
        self._fetch_result = fetch_result

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalar_one(self):
        return self._scalar_value

    def scalars(self):
        return self

    def all(self):
        return self._scalars_value

    @property
    def rowcount(self):
        return self._rowcount

    def fetchone(self):
        return self._fetch_result

    def fetchall(self):
        return self._fetch_result or []


@pytest.fixture
def mock_session():
    return MockAsyncSession()


@pytest.fixture
def sample_uuid():
    return uuid.uuid4()


@pytest.fixture
def sample_uuid2():
    return uuid.uuid4()


def create_mock_model_class():
    model_class = MagicMock()
    mock_id = MagicMock()
    mock_id.in_ = MagicMock(return_value=MagicMock())
    model_class.id = mock_id
    model_class.__table__ = MagicMock()
    model_class.__tablename__ = "mock_table"
    return model_class


class TestBaseRepository:
    """BaseRepository 单元测试"""

    @pytest.fixture
    def base_repo(self, mock_session, sample_uuid):
        model_class = create_mock_model_class()
        with patch.object(BaseRepository, '__init__', lambda self, model, session: None):
            repo = BaseRepository(MagicMock(), mock_session)
            repo._model = model_class
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_create(self, base_repo, mock_session, sample_uuid):
        mock_instance = MagicMock()
        mock_instance.id = sample_uuid
        base_repo._model = MagicMock(return_value=mock_instance)

        result = await base_repo.create(name="test", value=123)

        assert mock_instance == result
        mock_session.add.assert_called_once_with(mock_instance)
        await mock_session.flush()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, base_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value={"id": sample_uuid, "name": "test"})
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.get_by_id(sample_uuid)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, base_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.get_by_id(sample_uuid)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_one(self, base_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value={"id": sample_uuid})
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.get_one(name="test")
            assert result is not None

    @pytest.mark.asyncio
    async def test_find_all(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_all_with_filters(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4(), "status": "active"}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(filters={"status": "active"})
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_all_with_order(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4()}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(order_by="created_at", order_desc=True)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4()}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(limit=10, offset=5)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=5)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.count()
            assert result == 5

    @pytest.mark.asyncio
    async def test_count_with_filters(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=3)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.count(filters={"status": "active"})
            assert result == 3

    @pytest.mark.asyncio
    async def test_update_found(self, base_repo, mock_session, sample_uuid):
        mock_instance = MagicMock()
        mock_instance.id = sample_uuid
        mock_instance.name = "old_name"
        mock_result = MockSelectResult(scalar_value=mock_instance)
        mock_session.execute.return_value = mock_result

        with patch.object(base_repo, 'get_by_id', return_value=mock_instance):
            result = await base_repo.update(sample_uuid, name="new_name")
            assert result is not None

    @pytest.mark.asyncio
    async def test_update_not_found(self, base_repo, mock_session, sample_uuid):
        with patch.object(base_repo, 'get_by_id', return_value=None):
            result = await base_repo.update(sample_uuid, name="new_name")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self, base_repo, mock_session, sample_uuid):
        mock_instance = MagicMock()
        mock_instance.id = sample_uuid
        with patch.object(base_repo, 'get_by_id', return_value=mock_instance):
            result = await base_repo.delete(sample_uuid)
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, base_repo, mock_session, sample_uuid):
        with patch.object(base_repo, 'get_by_id', return_value=None):
            result = await base_repo.delete(sample_uuid)
            assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.exists(name="test")
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=0)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.exists(name="nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_bulk_create(self, base_repo, mock_session):
        instances = [{"name": "item1"}, {"name": "item2"}]
        mock_model = MagicMock()
        base_repo._model = mock_model

        result = await base_repo.bulk_create(instances)

        assert len(result) == 2
        assert mock_session.add.call_count == 2
        await mock_session.flush()

    @pytest.mark.asyncio
    async def test_bulk_update(self, base_repo, mock_session, sample_uuid):
        ids = [sample_uuid]
        mock_result = MockExecuteResult(rowcount=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.update'):
            result = await base_repo.bulk_update(ids, name="updated")
            assert result == 1

    @pytest.mark.asyncio
    async def test_bulk_update_empty_ids(self, base_repo, mock_session):
        result = await base_repo.bulk_update([], name="updated")
        assert result == 0

    @pytest.mark.asyncio
    async def test_bulk_delete(self, base_repo, mock_session, sample_uuid):
        ids = [sample_uuid]
        mock_result = MockExecuteResult(rowcount=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.delete'):
            result = await base_repo.bulk_delete(ids)
            assert result == 1

    @pytest.mark.asyncio
    async def test_bulk_delete_empty_ids(self, base_repo, mock_session):
        result = await base_repo.bulk_delete([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_by_ids(self, base_repo, mock_session, sample_uuid):
        mock_items = [{"id": sample_uuid}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.get_by_ids([sample_uuid])
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_ids_empty(self, base_repo, mock_session):
        result = await base_repo.get_by_ids([])
        assert result == []


class TestUserRepository:
    """UserRepository 单元测试"""

    @pytest.fixture
    def user_repo(self, mock_session):
        with patch.object(UserRepository, '__init__', lambda self, session: None):
            repo = UserRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_username(self, user_repo, mock_session):
        mock_user = MagicMock()
        with patch.object(user_repo, 'get_one', return_value=mock_user):
            result = await user_repo.get_by_username("testuser")
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_email(self, user_repo, mock_session):
        mock_user = MagicMock()
        with patch.object(user_repo, 'get_one', return_value=mock_user):
            result = await user_repo.get_by_email("test@example.com")
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_with_permissions(self, user_repo, mock_session, sample_uuid):
        mock_user = MagicMock()
        mock_user.id = sample_uuid
        mock_user.roles = []

        with patch.object(user_repo, 'get_with_permissions', return_value=mock_user):
            result = await user_repo.get_with_permissions(sample_uuid)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_create_user(self, user_repo, mock_session):
        mock_user = MagicMock()
        with patch.object(user_repo, 'create', return_value=mock_user):
            result = await user_repo.create_user(
                username="test",
                email="test@example.com",
                password_hash="hash"
            )
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_update_password(self, user_repo, mock_session, sample_uuid):
        mock_user = MagicMock()
        with patch.object(user_repo, 'update', return_value=mock_user):
            result = await user_repo.update_password(sample_uuid, "new_hash")
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_update_email(self, user_repo, mock_session, sample_uuid):
        mock_user = MagicMock()
        with patch.object(user_repo, 'update', return_value=mock_user):
            result = await user_repo.update_email(sample_uuid, "new@example.com")
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_remove_role_not_found(self, user_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.and_'):
                result = await user_repo.remove_role(sample_uuid, sample_uuid)
                assert result is False

    @pytest.mark.asyncio
    async def test_has_permission(self, user_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await user_repo.has_permission(sample_uuid, "projects", "read")
            assert result is True

    @pytest.mark.asyncio
    async def test_search_by_username(self, user_repo, mock_session):
        mock_users = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_users)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await user_repo.search_by_username("test")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_email(self, user_repo, mock_session):
        mock_users = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_users)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await user_repo.search_by_email("test")
            assert len(result) == 1


class TestRoleRepository:
    """RoleRepository 单元测试"""

    @pytest.fixture
    def role_repo(self, mock_session):
        with patch.object(RoleRepository, '__init__', lambda self, session: None):
            repo = RoleRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_name(self, role_repo, mock_session):
        mock_role = MagicMock()
        with patch.object(role_repo, 'get_one', return_value=mock_role):
            result = await role_repo.get_by_name("admin")
            assert result == mock_role

    @pytest.mark.asyncio
    async def test_remove_permission_not_found(self, role_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.and_'):
                result = await role_repo.remove_permission(sample_uuid, sample_uuid)
                assert result is False


class TestPermissionRepository:
    """PermissionRepository 单元测试"""

    @pytest.fixture
    def perm_repo(self, mock_session):
        with patch.object(PermissionRepository, '__init__', lambda self, session: None):
            repo = PermissionRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_resource_action(self, perm_repo, mock_session):
        mock_perm = MagicMock()
        with patch.object(perm_repo, 'get_one', return_value=mock_perm):
            result = await perm_repo.get_by_resource_action("projects", "read")
            assert result == mock_perm

    @pytest.mark.asyncio
    async def test_get_by_resource(self, perm_repo, mock_session):
        mock_perms = [MagicMock()]
        with patch.object(perm_repo, 'find_all', return_value=mock_perms):
            result = await perm_repo.get_by_resource("projects")
            assert result == mock_perms

    @pytest.mark.asyncio
    async def test_get_all_grouped_by_resource(self, perm_repo, mock_session):
        mock_perm1 = MagicMock()
        mock_perm1.resource = "projects"
        mock_perm1.action = "read"
        mock_perms = [mock_perm1]
        mock_result = MockSelectResult(scalars_value=mock_perms)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await perm_repo.get_all_grouped_by_resource()
            assert "projects" in result


class TestProjectRepository:
    """ProjectRepository 单元测试"""

    @pytest.fixture
    def project_repo(self, mock_session):
        with patch.object(ProjectRepository, '__init__', lambda self, session: None):
            repo = ProjectRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_owner(self, project_repo, mock_session, sample_uuid):
        mock_projects = [MagicMock()]
        with patch.object(project_repo, 'find_all', return_value=mock_projects):
            result = await project_repo.get_by_owner(sample_uuid)
            assert result == mock_projects

    @pytest.mark.asyncio
    async def test_get_by_status(self, project_repo, mock_session):
        mock_projects = [MagicMock()]
        with patch.object(project_repo, 'find_all', return_value=mock_projects):
            result = await project_repo.get_by_status("active")
            assert result == mock_projects

    @pytest.mark.asyncio
    async def test_create_project(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        with patch.object(project_repo, 'create', return_value=mock_project):
            result = await project_repo.create_project(
                name="Test Project",
                owner_id=sample_uuid
            )
            assert result == mock_project

    @pytest.mark.asyncio
    async def test_update_progress(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        with patch.object(project_repo, 'update', return_value=mock_project):
            result = await project_repo.update_progress(sample_uuid, 50)
            assert result == mock_project

    @pytest.mark.asyncio
    async def test_update_status(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        with patch.object(project_repo, 'update', return_value=mock_project):
            result = await project_repo.update_status(sample_uuid, "completed")
            assert result == mock_project

    @pytest.mark.asyncio
    async def test_increment_chapter_count(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_project.total_chapters = 5
        with patch.object(project_repo, 'get_by_id', return_value=mock_project):
            with patch.object(project_repo, 'update', return_value=mock_project):
                result = await project_repo.increment_chapter_count(sample_uuid)
                assert result is not None

    @pytest.mark.asyncio
    async def test_decrement_chapter_count(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_project.total_chapters = 5
        with patch.object(project_repo, 'get_by_id', return_value=mock_project):
            with patch.object(project_repo, 'update', return_value=mock_project):
                result = await project_repo.decrement_chapter_count(sample_uuid)
                assert result is not None

    @pytest.mark.asyncio
    async def test_search_by_name(self, project_repo, mock_session):
        mock_projects = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_projects)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            result = await project_repo.search_by_name("test")
            assert len(result) == 1


class TestProjectMemberRepository:
    """ProjectMemberRepository 单元测试"""

    @pytest.fixture
    def member_repo(self, mock_session):
        with patch.object(ProjectMemberRepository, '__init__', lambda self, session: None):
            repo = ProjectMemberRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_add_member(self, member_repo, mock_session, sample_uuid):
        mock_member = MagicMock()
        with patch.object(member_repo, 'create', return_value=mock_member):
            result = await member_repo.add_member(sample_uuid, sample_uuid, "editor")
            assert result == mock_member

    @pytest.mark.asyncio
    async def test_is_member_true(self, member_repo, mock_session, sample_uuid):
        with patch.object(member_repo, 'exists', return_value=True):
            result = await member_repo.is_member(sample_uuid, sample_uuid)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_member_false(self, member_repo, mock_session, sample_uuid):
        with patch.object(member_repo, 'exists', return_value=False):
            result = await member_repo.is_member(sample_uuid, sample_uuid)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_member_role(self, member_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value="editor")
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.and_'):
                result = await member_repo.get_member_role(sample_uuid, sample_uuid)
                assert result == "editor"

    @pytest.mark.asyncio
    async def test_update_member_role(self, member_repo, mock_session, sample_uuid):
        mock_member = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_member)
        mock_session.execute.return_value = mock_result

        with patch.object(member_repo, 'get_one', return_value=mock_member):
            result = await member_repo.update_member_role(sample_uuid, sample_uuid, "admin")
            assert result is not None

    @pytest.mark.asyncio
    async def test_remove_member_not_found(self, member_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.and_'):
                result = await member_repo.remove_member(sample_uuid, sample_uuid)
                assert result is False


class TestChapterRepository:
    """ChapterRepository 单元测试"""

    @pytest.fixture
    def chapter_repo(self, mock_session):
        with patch.object(ChapterRepository, '__init__', lambda self, session: None):
            repo = ChapterRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_project(self, chapter_repo, mock_session, sample_uuid):
        mock_chapters = [MagicMock()]
        with patch.object(chapter_repo, 'find_all', return_value=mock_chapters):
            result = await chapter_repo.get_by_project(sample_uuid)
            assert result == mock_chapters

    @pytest.mark.asyncio
    async def test_create_chapter(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        with patch.object(chapter_repo, 'create', return_value=mock_chapter):
            result = await chapter_repo.create_chapter(
                project_id=sample_uuid,
                title="Test Chapter",
                order_num=1,
                version="1.0"
            )
            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_update_status(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        with patch.object(chapter_repo, 'update', return_value=mock_chapter):
            result = await chapter_repo.update_status(sample_uuid, "published")
            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_update_content_hash(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        with patch.object(chapter_repo, 'update', return_value=mock_chapter):
            result = await chapter_repo.update_content_hash(sample_uuid, "abc123")
            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_update_word_count(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        with patch.object(chapter_repo, 'update', return_value=mock_chapter):
            result = await chapter_repo.update_word_count(sample_uuid, 1000)
            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_by_parent(self, chapter_repo, mock_session, sample_uuid):
        mock_chapters = [MagicMock()]
        with patch.object(chapter_repo, 'find_all', return_value=mock_chapters):
            result = await chapter_repo.get_by_parent(sample_uuid)
            assert result == mock_chapters

    @pytest.mark.asyncio
    async def test_get_next_order_num(self, chapter_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=5)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            result = await chapter_repo.get_next_order_num(sample_uuid)
            assert result == 6

    @pytest.mark.asyncio
    async def test_reorder_chapters(self, chapter_repo, mock_session, sample_uuid):
        chapter_orders = [{"id": sample_uuid, "order_num": 1}]
        mock_chapter = MagicMock()

        # Mock the begin context manager
        mock_begin_ctx = MagicMock()
        mock_begin_ctx.__aenter__ = AsyncMock(return_value=None)
        mock_begin_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin_ctx)

        with patch.object(chapter_repo, 'update', return_value=mock_chapter):
            await chapter_repo.reorder_chapters(sample_uuid, chapter_orders)


class TestChapterContentRepository:
    """ChapterContentRepository 单元测试"""

    @pytest.fixture
    def content_repo(self, mock_session):
        with patch.object(ChapterContentRepository, '__init__', lambda self, session: None):
            repo = ChapterContentRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_chapter(self, content_repo, mock_session, sample_uuid):
        mock_contents = [MagicMock()]
        with patch.object(content_repo, 'find_all', return_value=mock_contents):
            result = await content_repo.get_by_chapter(sample_uuid)
            assert result == mock_contents

    @pytest.mark.asyncio
    async def test_get_latest(self, content_repo, mock_session, sample_uuid):
        mock_content = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_content)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            result = await content_repo.get_latest(sample_uuid)
            assert result == mock_content

    @pytest.mark.asyncio
    async def test_create_content(self, content_repo, mock_session, sample_uuid):
        mock_content = MagicMock()
        with patch.object(content_repo, 'create', return_value=mock_content):
            result = await content_repo.create_content(
                chapter_id=sample_uuid,
                content="Test content",
                version="1.0",
                content_hash="abc123"
            )
            assert result == mock_content

    @pytest.mark.asyncio
    async def test_get_by_hash(self, content_repo, mock_session, sample_uuid):
        mock_content = MagicMock()
        with patch.object(content_repo, 'get_one', return_value=mock_content):
            result = await content_repo.get_by_hash(sample_uuid, "abc123")
            assert result == mock_content


class TestSectionRepository:
    """SectionRepository 单元测试"""

    @pytest.fixture
    def section_repo(self, mock_session):
        with patch.object(SectionRepository, '__init__', lambda self, session: None):
            repo = SectionRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_chapter(self, section_repo, mock_session, sample_uuid):
        mock_sections = [MagicMock()]
        with patch.object(section_repo, 'find_all', return_value=mock_sections):
            result = await section_repo.get_by_chapter(sample_uuid)
            assert result == mock_sections

    @pytest.mark.asyncio
    async def test_get_child_sections(self, section_repo, mock_session, sample_uuid):
        mock_sections = [MagicMock()]
        with patch.object(section_repo, 'find_all', return_value=mock_sections):
            result = await section_repo.get_child_sections(sample_uuid)
            assert result == mock_sections

    @pytest.mark.asyncio
    async def test_create_section(self, section_repo, mock_session, sample_uuid):
        mock_section = MagicMock()
        with patch.object(section_repo, 'create', return_value=mock_section):
            result = await section_repo.create_section(
                chapter_id=sample_uuid,
                title="Test Section",
                order_num=1
            )
            assert result == mock_section

    @pytest.mark.asyncio
    async def test_get_next_order_num(self, section_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=3)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            result = await section_repo.get_next_order_num(sample_uuid)
            assert result == 4


class TestAuditLogRepository:
    """AuditLogRepository 单元测试"""

    @pytest.fixture
    def audit_repo(self, mock_session):
        with patch.object(AuditLogRepository, '__init__', lambda self, session: None):
            repo = AuditLogRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_user(self, audit_repo, mock_session, sample_uuid):
        mock_logs = [MagicMock()]
        with patch.object(audit_repo, 'find_all', return_value=mock_logs):
            result = await audit_repo.get_by_user(sample_uuid)
            assert result == mock_logs

    @pytest.mark.asyncio
    async def test_get_by_resource(self, audit_repo, mock_session, sample_uuid):
        mock_logs = [MagicMock()]
        with patch.object(audit_repo, 'find_all', return_value=mock_logs):
            result = await audit_repo.get_by_resource("project", sample_uuid)
            assert result == mock_logs

    @pytest.mark.asyncio
    async def test_get_by_event_type(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        with patch.object(audit_repo, 'find_all', return_value=mock_logs):
            result = await audit_repo.get_by_event_type("login")
            assert result == mock_logs

    @pytest.mark.asyncio
    async def test_get_recent_logs(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            result = await audit_repo.get_recent_logs(hours=24)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs(self, audit_repo, mock_session, sample_uuid):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.search_logs(
                    event_type="login",
                    user_id=sample_uuid
                )
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_log(self, audit_repo, mock_session, sample_uuid):
        mock_log = MagicMock()
        with patch.object(audit_repo, 'create', return_value=mock_log):
            result = await audit_repo.create_log(
                event_type="login",
                user_id=sample_uuid
            )
            assert result == mock_log

    @pytest.mark.asyncio
    async def test_count_by_event_type(self, audit_repo, mock_session):
        with patch.object(audit_repo, 'count', return_value=5):
            result = await audit_repo.count_by_event_type("login")
            assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_user(self, audit_repo, mock_session, sample_uuid):
        with patch.object(audit_repo, 'count', return_value=10):
            result = await audit_repo.count_by_user(sample_uuid)
            assert result == 10

    @pytest.mark.asyncio
    async def test_get_failed_actions(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.get_failed_actions()
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_ip_address(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.get_by_ip_address("192.168.1.1")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_verify_signature_valid(self, audit_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value="valid_signature")
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            result = await audit_repo.verify_signature(sample_uuid, "valid_signature")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid(self, audit_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value="other_signature")
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            result = await audit_repo.verify_signature(sample_uuid, "wrong_signature")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_signature_not_found(self, audit_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            result = await audit_repo.verify_signature(sample_uuid, "any_signature")
            assert result is False


class TestTermRepository:
    """TermRepository 单元测试"""

    @pytest.fixture
    def term_repo(self, mock_session):
        with patch.object(TermRepository, '__init__', lambda self, session: None):
            repo = TermRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_term(self, term_repo, mock_session):
        mock_term = MagicMock()
        with patch.object(term_repo, 'get_one', return_value=mock_term):
            result = await term_repo.get_by_term("test")
            assert result == mock_term

    @pytest.mark.asyncio
    async def test_get_by_domain(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        with patch.object(term_repo, 'find_all', return_value=mock_terms):
            result = await term_repo.get_by_domain("science")
            assert result == mock_terms

    @pytest.mark.asyncio
    async def test_get_locked_terms(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        with patch.object(term_repo, 'find_all', return_value=mock_terms):
            result = await term_repo.get_locked_terms()
            assert result == mock_terms

    @pytest.mark.asyncio
    async def test_get_unlocked_terms(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        with patch.object(term_repo, 'find_all', return_value=mock_terms):
            result = await term_repo.get_unlocked_terms()
            assert result == mock_terms

    @pytest.mark.asyncio
    async def test_search_by_term(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_terms)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.term_repository.select'):
            with patch('db.repositories.term_repository.or_'):
                result = await term_repo.search_by_term("test")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_definition(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_terms)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.term_repository.select'):
            result = await term_repo.search_by_definition("definition query")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_term(self, term_repo, mock_session):
        mock_term = MagicMock()
        with patch.object(term_repo, 'create', return_value=mock_term):
            result = await term_repo.create_term(
                term="test",
                definition="test definition"
            )
            assert result == mock_term

    @pytest.mark.asyncio
    async def test_lock_term(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        with patch.object(term_repo, 'update', return_value=mock_term):
            result = await term_repo.lock_term(sample_uuid)
            assert result == mock_term

    @pytest.mark.asyncio
    async def test_unlock_term(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        with patch.object(term_repo, 'update', return_value=mock_term):
            result = await term_repo.unlock_term(sample_uuid)
            assert result == mock_term

    @pytest.mark.asyncio
    async def test_add_synonym(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.synonyms = []
        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.add_synonym(sample_uuid, "new_synonym")
            assert result is not None

    @pytest.mark.asyncio
    async def test_add_synonym_not_found(self, term_repo, mock_session, sample_uuid):
        with patch.object(term_repo, 'get_by_id', return_value=None):
            result = await term_repo.add_synonym(sample_uuid, "new_synonym")
            assert result is None

    @pytest.mark.asyncio
    async def test_remove_synonym(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.synonyms = ["existing"]
        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.remove_synonym(sample_uuid, "existing")
            assert result is not None

    @pytest.mark.asyncio
    async def test_find_similar_terms(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = ["synonym1"]
        mock_term.domain = "science"

        mock_similar = MagicMock()
        mock_similar.id = uuid.uuid4()
        mock_similar.synonyms = ["synonym1"]
        mock_similar.domain = "science"

        # Set up mock_session.execute to return proper result
        mock_result = MockSelectResult(scalars_value=[mock_similar])
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert len(result) == 1


class TestConceptRepository:
    """ConceptRepository 单元测试"""

    @pytest.fixture
    def concept_repo(self, mock_session):
        with patch.object(ConceptRepository, '__init__', lambda self, session: None):
            repo = ConceptRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_name(self, concept_repo, mock_session):
        mock_concept = MagicMock()
        with patch.object(concept_repo, 'get_one', return_value=mock_concept):
            result = await concept_repo.get_by_name("test")
            assert result == mock_concept

    @pytest.mark.asyncio
    async def test_get_by_domain(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        with patch.object(concept_repo, 'find_all', return_value=mock_concepts):
            result = await concept_repo.get_by_domain("science")
            assert result == mock_concepts

    @pytest.mark.asyncio
    async def test_get_locked_concepts(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        with patch.object(concept_repo, 'find_all', return_value=mock_concepts):
            result = await concept_repo.get_locked_concepts()
            assert result == mock_concepts

    @pytest.mark.asyncio
    async def test_get_unlocked_concepts(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        with patch.object(concept_repo, 'find_all', return_value=mock_concepts):
            result = await concept_repo.get_unlocked_concepts()
            assert result == mock_concepts

    @pytest.mark.asyncio
    async def test_search_by_name(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_concepts)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.term_repository.select'):
            with patch('db.repositories.term_repository.or_'):
                result = await concept_repo.search_by_name("test")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_definition(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_concepts)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.term_repository.select'):
            result = await concept_repo.search_by_definition("definition query")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_concept(self, concept_repo, mock_session):
        mock_concept = MagicMock()
        with patch.object(concept_repo, 'create', return_value=mock_concept):
            result = await concept_repo.create_concept(
                name="test",
                definition="test definition"
            )
            assert result == mock_concept

    @pytest.mark.asyncio
    async def test_lock_concept(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        with patch.object(concept_repo, 'update', return_value=mock_concept):
            result = await concept_repo.lock_concept(sample_uuid)
            assert result == mock_concept

    @pytest.mark.asyncio
    async def test_unlock_concept(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        with patch.object(concept_repo, 'update', return_value=mock_concept):
            result = await concept_repo.unlock_concept(sample_uuid)
            assert result == mock_concept

    @pytest.mark.asyncio
    async def test_get_by_source_chapter(self, concept_repo, mock_session, sample_uuid):
        mock_concepts = [MagicMock()]
        with patch.object(concept_repo, 'find_all', return_value=mock_concepts):
            result = await concept_repo.get_by_source_chapter(sample_uuid)
            assert result == mock_concepts

    @pytest.mark.asyncio
    async def test_add_related_term(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        mock_concept.related_terms = []
        with patch.object(concept_repo, 'get_by_id', return_value=mock_concept):
            result = await concept_repo.add_related_term(sample_uuid, "new_term")
            assert result is not None

    @pytest.mark.asyncio
    async def test_remove_related_term(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        mock_concept.related_terms = ["existing"]
        with patch.object(concept_repo, 'get_by_id', return_value=mock_concept):
            result = await concept_repo.remove_related_term(sample_uuid, "existing")
            assert result is not None


class TestKnowledgeGraphRepositoryMethods:
    """KnowledgeGraphRepository 方法测试 - 不触发模型初始化"""

    @pytest.fixture
    def kg_repo(self, mock_session):
        with patch.object(KnowledgeGraphRepository, '__init__', lambda self, session: None):
            repo = KnowledgeGraphRepository(mock_session)
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_outgoing_edges(self, kg_repo, mock_session):
        mock_edges = [MagicMock()]
        with patch.object(kg_repo, 'get_edges', return_value=mock_edges):
            result = await kg_repo.get_outgoing_edges("node1")
            assert result == mock_edges

    @pytest.mark.asyncio
    async def test_get_incoming_edges(self, kg_repo, mock_session):
        mock_edges = [MagicMock()]
        with patch.object(kg_repo, 'get_edges', return_value=mock_edges):
            result = await kg_repo.get_incoming_edges("node1")
            assert result == mock_edges

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_1(self, kg_repo, mock_session):
        mock_edge = MagicMock()
        mock_edge.target_id = "node2"
        mock_edge.edge_type = "KNOWS"
        mock_edge.properties = {}

        with patch.object(kg_repo, 'get_edges', return_value=[mock_edge]):
            result = await kg_repo.get_neighbors("node1", depth=1)
            assert len(result) == 1
            assert result[0]["neighbor_id"] == "node2"

    @pytest.mark.asyncio
    async def test_count_nodes(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=10)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.count_nodes()
            assert result == 10

    @pytest.mark.asyncio
    async def test_count_nodes_with_type(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=5)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.count_nodes(node_type="person")
            assert result == 5

    @pytest.mark.asyncio
    async def test_count_edges(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=20)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.count_edges()
            assert result == 20

    @pytest.mark.asyncio
    async def test_node_exists_true(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.node_exists("node1")
            assert result is True

    @pytest.mark.asyncio
    async def test_node_exists_false(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=0)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.node_exists("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_edge_exists_true(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                result = await kg_repo.edge_exists("node1", "node2", "KNOWS")
                assert result is True

    @pytest.mark.asyncio
    async def test_edge_exists_false(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=0)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                result = await kg_repo.edge_exists("node1", "node2", "KNOWS")
                assert result is False

    @pytest.mark.asyncio
    async def test_create_node(self, kg_repo, mock_session):
        mock_node = MagicMock()
        mock_session.refresh = AsyncMock(return_value=mock_node)

        with patch('db.repositories.knowledge_graph_repository.GraphNode') as MockGraphNode:
            MockGraphNode.return_value = mock_node
            result = await kg_repo.create_node(
                node_id="node1",
                node_type="person",
                properties={"name": "John"}
            )
            assert result == mock_node
            mock_session.add.assert_called_once_with(mock_node)
            await mock_session.flush()

    @pytest.mark.asyncio
    async def test_get_node_found(self, kg_repo, mock_session):
        mock_node = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_node)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_node("node1")
            assert result == mock_node

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_node("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_all_nodes(self, kg_repo, mock_session):
        mock_nodes = [MagicMock(), MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_nodes)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_all_nodes()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_nodes_with_type(self, kg_repo, mock_session):
        mock_nodes = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_nodes)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_all_nodes(node_type="person")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_node_found(self, kg_repo, mock_session):
        mock_node = MagicMock()
        mock_node.properties = {}
        mock_result = MockSelectResult(scalar_value=mock_node)
        mock_session.execute.return_value = mock_result

        with patch.object(kg_repo, 'get_node', return_value=mock_node):
            result = await kg_repo.update_node("node1", {"name": "Updated"})
            assert result == mock_node
            assert mock_node.properties == {"name": "Updated"}

    @pytest.mark.asyncio
    async def test_update_node_not_found(self, kg_repo, mock_session):
        with patch.object(kg_repo, 'get_node', return_value=None):
            result = await kg_repo.update_node("nonexistent", {"name": "Updated"})
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_node_found(self, kg_repo, mock_session):
        mock_node = MagicMock()
        with patch.object(kg_repo, 'get_node', return_value=mock_node):
            result = await kg_repo.delete_node("node1")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_node_not_found(self, kg_repo, mock_session):
        with patch.object(kg_repo, 'get_node', return_value=None):
            result = await kg_repo.delete_node("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_create_edge_success(self, kg_repo, mock_session):
        mock_source = MagicMock()
        mock_target = MagicMock()
        mock_edge = MagicMock()

        with patch.object(kg_repo, 'get_node', side_effect=[mock_source, mock_target]):
            with patch('db.repositories.knowledge_graph_repository.GraphEdge', return_value=mock_edge):
                result = await kg_repo.create_edge(
                    source_id="node1",
                    target_id="node2",
                    edge_type="KNOWS"
                )
                assert result == mock_edge

    @pytest.mark.asyncio
    async def test_create_edge_source_not_found(self, kg_repo, mock_session):
        with patch.object(kg_repo, 'get_node', return_value=None):
            result = await kg_repo.create_edge(
                source_id="nonexistent",
                target_id="node2",
                edge_type="KNOWS"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_get_edge_found(self, kg_repo, mock_session):
        mock_edge = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_edge)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_edge(1)
            assert result == mock_edge

    @pytest.mark.asyncio
    async def test_get_edge_not_found(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.get_edge(999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_edges_with_filters(self, kg_repo, mock_session):
        mock_edges = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_edges)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                result = await kg_repo.get_edges(source_id="node1", edge_type="KNOWS")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_edge_found(self, kg_repo, mock_session):
        mock_edge = MagicMock()
        with patch.object(kg_repo, 'get_edge', return_value=mock_edge):
            result = await kg_repo.delete_edge(1)
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_edge_not_found(self, kg_repo, mock_session):
        with patch.object(kg_repo, 'get_edge', return_value=None):
            result = await kg_repo.delete_edge(999)
            assert result is False

    @pytest.mark.asyncio
    async def test_batch_insert_nodes(self, kg_repo, mock_session):
        nodes = [
            {"id": "node1", "node_type": "person", "properties": {}},
            {"id": "node2", "node_type": "org", "properties": {"name": "Test"}},
        ]

        with patch('db.repositories.knowledge_graph_repository.GraphNode') as MockGraphNode:
            MockGraphNode.side_effect = lambda **kw: MagicMock(**kw)
            result = await kg_repo.batch_insert_nodes(nodes)
            assert result == 2

    @pytest.mark.asyncio
    async def test_batch_insert_edges(self, kg_repo, mock_session):
        edges = [
            {"source_id": "node1", "target_id": "node2", "edge_type": "KNOWS", "properties": {}},
        ]

        with patch('db.repositories.knowledge_graph_repository.GraphEdge') as MockGraphEdge:
            MockGraphEdge.side_effect = lambda **kw: MagicMock(**kw)
            result = await kg_repo.batch_insert_edges(edges)
            assert result == 1

    @pytest.mark.asyncio
    async def test_query_nodes_with_type_and_props(self, kg_repo, mock_session):
        mock_nodes = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_nodes)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                with patch('db.repositories.knowledge_graph_repository.text'):
                    result = await kg_repo.query_nodes(node_type="person", name="John")
                    assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_nodes_no_filters(self, kg_repo, mock_session):
        mock_nodes = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_nodes)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.query_nodes()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_2(self, kg_repo, mock_session):
        mock_rows = [
            ("node2", "KNOWS", {}, 1),
            ("node3", "KNOWS", {}, 2),
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.text'):
            result = await kg_repo.get_neighbors("node1", depth=2)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_path_found(self, kg_repo, mock_session):
        mock_row = (["node1", "node2", "node3"],)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.text'):
            result = await kg_repo.find_path("node1", "node3")
            assert result == ["node1", "node2", "node3"]

    @pytest.mark.asyncio
    async def test_find_path_not_found(self, kg_repo, mock_session):
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.text'):
            result = await kg_repo.find_path("node1", "node999")
            assert result is None

    @pytest.mark.asyncio
    async def test_find_path_same_node(self, kg_repo, mock_session):
        result = await kg_repo.find_path("node1", "node1")
        assert result == ["node1"]

    @pytest.mark.asyncio
    async def test_bfs_traverse(self, kg_repo, mock_session):
        mock_rows = [
            ("node2", 1),
            ("node3", 1),
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.text'):
            result = await kg_repo.bfs_traverse("node1")
            assert "node1" in result

    @pytest.mark.asyncio
    async def test_dfs_traverse(self, kg_repo, mock_session):
        mock_edge = MagicMock()
        mock_edge.target_id = "node2"

        mock_incoming = MagicMock()
        mock_incoming.source_id = "node3"

        call_count = [0]
        async def get_edges_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [mock_edge]
            return [mock_incoming]

        with patch.object(kg_repo, 'get_edges', side_effect=get_edges_side_effect):
            result = await kg_repo.dfs_traverse("node1")
            assert "node1" in result

    @pytest.mark.asyncio
    async def test_get_edges_empty_result(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalars_value=[])
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                result = await kg_repo.get_edges(source_id="nonexistent")
                assert len(result) == 0


class TestUserRepositoryMore:
    """UserRepository 更多方法测试"""

    @pytest.fixture
    def user_repo(self, mock_session):
        with patch.object(UserRepository, '__init__', lambda self, session: None):
            repo = UserRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_roles(self, user_repo, mock_session, sample_uuid):
        mock_user = MagicMock()
        mock_user.roles = []
        mock_result = MockSelectResult(scalar_value=mock_user)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.selectinload'):
                result = await user_repo.get_with_roles(sample_uuid)
                assert result == mock_user

    @pytest.mark.asyncio
    async def test_assign_role(self, user_repo, mock_session, sample_uuid):
        mock_user_role = MagicMock()
        mock_session.refresh = AsyncMock(return_value=mock_user_role)

        with patch('db.repositories.user_repository.UserRole') as MockUserRole:
            MockUserRole.return_value = mock_user_role
            result = await user_repo.assign_role(sample_uuid, sample_uuid)
            assert result == mock_user_role


class TestRoleRepositoryMore:
    """RoleRepository 更多方法测试"""

    @pytest.fixture
    def role_repo(self, mock_session):
        with patch.object(RoleRepository, '__init__', lambda self, session: None):
            repo = RoleRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_permissions(self, role_repo, mock_session, sample_uuid):
        mock_role = MagicMock()
        mock_role.permissions = []
        mock_result = MockSelectResult(scalar_value=mock_role)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.selectinload'):
                result = await role_repo.get_with_permissions(sample_uuid)
                assert result == mock_role

    @pytest.mark.asyncio
    async def test_get_all_with_user_count(self, role_repo, mock_session):
        mock_roles = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_roles)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.selectinload'):
                result = await role_repo.get_all_with_user_count()
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_assign_permission(self, role_repo, mock_session, sample_uuid):
        mock_role_perm = MagicMock()
        mock_session.refresh = AsyncMock(return_value=mock_role_perm)

        with patch('db.repositories.user_repository.RolePermission') as MockRolePermission:
            MockRolePermission.return_value = mock_role_perm
            result = await role_repo.assign_permission(sample_uuid, sample_uuid)
            assert result == mock_role_perm


class TestProjectRepositoryMore:
    """ProjectRepository 更多方法测试"""

    @pytest.fixture
    def project_repo(self, mock_session):
        with patch.object(ProjectRepository, '__init__', lambda self, session: None):
            repo = ProjectRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_owner(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_project)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.joinedload'):
                result = await project_repo.get_with_owner(sample_uuid)
                assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_with_members(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_project)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.selectinload'):
                result = await project_repo.get_with_members(sample_uuid)
                assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_with_chapters(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_project)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.selectinload'):
                result = await project_repo.get_with_chapters(sample_uuid)
                assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_full_project(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_project)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.joinedload'):
                with patch('db.repositories.project_repository.selectinload'):
                    result = await project_repo.get_full_project(sample_uuid)
                    assert result == mock_project


class TestChapterRepositoryMore:
    """ChapterRepository 更多方法测试"""

    @pytest.fixture
    def chapter_repo(self, mock_session):
        with patch.object(ChapterRepository, '__init__', lambda self, session: None):
            repo = ChapterRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_contents(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_chapter)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            with patch('db.repositories.chapter_repository.selectinload'):
                result = await chapter_repo.get_with_contents(sample_uuid)
                assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_with_sections(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_chapter)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            with patch('db.repositories.chapter_repository.selectinload'):
                result = await chapter_repo.get_with_sections(sample_uuid)
                assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_with_reviews(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_chapter)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            with patch('db.repositories.chapter_repository.selectinload'):
                result = await chapter_repo.get_with_reviews(sample_uuid)
                assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_full_chapter(self, chapter_repo, mock_session, sample_uuid):
        mock_chapter = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_chapter)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            with patch('db.repositories.chapter_repository.selectinload'):
                result = await chapter_repo.get_full_chapter(sample_uuid)
                assert result == mock_chapter


class TestAuditLogRepositoryMore:
    """AuditLogRepository 更多方法测试"""

    @pytest.fixture
    def audit_repo(self, mock_session):
        with patch.object(AuditLogRepository, '__init__', lambda self, session: None):
            repo = AuditLogRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_event_type_with_since(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=1)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.get_by_event_type("login", since=since)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count_by_event_type_with_since(self, audit_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=10)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=1)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.count_by_event_type("login", since=since)
                assert result == 10

    @pytest.mark.asyncio
    async def test_count_by_user_with_since(self, audit_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=5)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=1)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.count_by_user(sample_uuid, since=since)
                assert result == 5

    @pytest.mark.asyncio
    async def test_search_logs_with_multiple_filters(self, audit_repo, mock_session, sample_uuid):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=24)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.search_logs(
                    event_type="login",
                    user_id=sample_uuid,
                    action="create",
                    since=since,
                    limit=50
                )
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_no_filters(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            result = await audit_repo.search_logs(limit=10)
            assert len(result) == 1


class TestSectionRepositoryMore:
    """SectionRepository 更多方法测试"""

    @pytest.fixture
    def section_repo(self, mock_session):
        with patch.object(SectionRepository, '__init__', lambda self, session: None):
            repo = SectionRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_parent(self, section_repo, mock_session, sample_uuid):
        mock_section = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_section)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.chapter_repository.select'):
            with patch('db.repositories.chapter_repository.joinedload'):
                result = await section_repo.get_with_parent(sample_uuid)
                assert result == mock_section


class TestBaseRepositoryEdgeCases:
    """BaseRepository 边界情况测试"""

    @pytest.fixture
    def base_repo(self, mock_session, sample_uuid):
        model_class = create_mock_model_class()
        with patch.object(BaseRepository, '__init__', lambda self, model, session: None):
            repo = BaseRepository(MagicMock(), mock_session)
            repo._model = model_class
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_find_all_offset_with_row_number(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4()}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(offset_with_row_number=True)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_exists_with_none_value(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.exists(status=None)
            assert result is True

    @pytest.mark.asyncio
    async def test_count_with_none_value(self, base_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=2)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.count(filters={"status": None})
            assert result == 2

    @pytest.mark.asyncio
    async def test_find_all_with_none_filter_value(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4(), "status": None}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(filters={"status": None})
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_all_order_asc(self, base_repo, mock_session):
        mock_items = [{"id": uuid.uuid4()}]
        mock_result = MockSelectResult(scalars_value=mock_items)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.base_repository.select'):
            result = await base_repo.find_all(order_by="created_at", order_desc=False)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_bulk_create_refresh(self, base_repo, mock_session):
        instances = [{"name": "item1"}, {"name": "item2"}]
        mock_model = MagicMock()
        base_repo._model = mock_model
        mock_instance = MagicMock()
        mock_model.side_effect = [mock_instance, mock_instance]

        result = await base_repo.bulk_create(instances)

        assert len(result) == 2
        assert mock_session.refresh.call_count == 2


class TestUserRepositoryEdgeCases:
    """UserRepository 边界情况测试"""

    @pytest.fixture
    def user_repo(self, mock_session):
        with patch.object(UserRepository, '__init__', lambda self, session: None):
            repo = UserRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_with_permissions_user_not_found(self, user_repo, mock_session, sample_uuid):
        with patch.object(user_repo, 'get_with_permissions', return_value=None):
            result = await user_repo.get_with_permissions(sample_uuid)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_with_permissions_with_roles(self, user_repo, mock_session, sample_uuid):
        mock_user = MagicMock()
        mock_user.id = sample_uuid
        mock_role = MagicMock()
        mock_role.id = sample_uuid
        mock_user.roles = [mock_role]

        with patch.object(user_repo, 'get_with_permissions', return_value=mock_user):
            result = await user_repo.get_with_permissions(sample_uuid)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_remove_role_found(self, user_repo, mock_session, sample_uuid):
        mock_user_role = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_user_role)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.and_'):
                result = await user_repo.remove_role(sample_uuid, sample_uuid)
                assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_true(self, user_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=1)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await user_repo.has_permission(sample_uuid, "projects", "read")
            assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_false(self, user_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=0)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            result = await user_repo.has_permission(sample_uuid, "projects", "delete")
            assert result is False


class TestRoleRepositoryEdgeCases:
    """RoleRepository 边界情况测试"""

    @pytest.fixture
    def role_repo(self, mock_session):
        with patch.object(RoleRepository, '__init__', lambda self, session: None):
            repo = RoleRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_remove_permission_found(self, role_repo, mock_session, sample_uuid):
        mock_role_perm = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_role_perm)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.user_repository.select'):
            with patch('db.repositories.user_repository.and_'):
                result = await role_repo.remove_permission(sample_uuid, sample_uuid)
                assert result is True


class TestPermissionRepositoryEdgeCases:
    """PermissionRepository 边界情况测试"""

    @pytest.fixture
    def perm_repo(self, mock_session):
        with patch.object(PermissionRepository, '__init__', lambda self, session: None):
            repo = PermissionRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo


class TestProjectRepositoryEdgeCases:
    """ProjectRepository 边界情况测试"""

    @pytest.fixture
    def project_repo(self, mock_session):
        with patch.object(ProjectRepository, '__init__', lambda self, session: None):
            repo = ProjectRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.fixture
    def member_repo(self, mock_session):
        with patch.object(ProjectMemberRepository, '__init__', lambda self, session: None):
            repo = ProjectMemberRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_owner_with_status(self, project_repo, mock_session, sample_uuid):
        mock_projects = [MagicMock()]
        with patch.object(project_repo, 'find_all', return_value=mock_projects):
            result = await project_repo.get_by_owner(sample_uuid, status="active")
            assert result == mock_projects

    @pytest.mark.asyncio
    async def test_increment_chapter_count_not_found(self, project_repo, mock_session, sample_uuid):
        with patch.object(project_repo, 'get_by_id', return_value=None):
            result = await project_repo.increment_chapter_count(sample_uuid)
            assert result is None

    @pytest.mark.asyncio
    async def test_decrement_chapter_count_zero(self, project_repo, mock_session, sample_uuid):
        mock_project = MagicMock()
        mock_project.total_chapters = 0
        with patch.object(project_repo, 'get_by_id', return_value=mock_project):
            result = await project_repo.decrement_chapter_count(sample_uuid)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_members_of_project(self, member_repo, mock_session, sample_uuid):
        mock_members = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_members)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.joinedload'):
                result = await member_repo.get_members_of_project(sample_uuid)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_projects_of_user(self, member_repo, mock_session, sample_uuid):
        mock_members = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_members)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.joinedload'):
                result = await member_repo.get_projects_of_user(sample_uuid)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_member_role_not_found(self, member_repo, mock_session, sample_uuid):
        mock_result = MockSelectResult(scalar_value=None)
        mock_session.execute.return_value = mock_result

        with patch.object(member_repo, 'get_one', return_value=None):
            result = await member_repo.update_member_role(sample_uuid, sample_uuid, "admin")
            assert result is None

    @pytest.mark.asyncio
    async def test_remove_member_found(self, member_repo, mock_session, sample_uuid):
        mock_member = MagicMock()
        mock_result = MockSelectResult(scalar_value=mock_member)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.project_repository.select'):
            with patch('db.repositories.project_repository.and_'):
                result = await member_repo.remove_member(sample_uuid, sample_uuid)
                assert result is True


class TestChapterRepositoryEdgeCases:
    """ChapterRepository 边界情况测试"""

    @pytest.fixture
    def chapter_repo(self, mock_session):
        with patch.object(ChapterRepository, '__init__', lambda self, session: None):
            repo = ChapterRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_project_with_status(self, chapter_repo, mock_session, sample_uuid):
        mock_chapters = [MagicMock()]
        with patch.object(chapter_repo, 'find_all', return_value=mock_chapters):
            result = await chapter_repo.get_by_project(sample_uuid, status="published")
            assert result == mock_chapters


class TestTermRepositoryEdgeCases:
    """TermRepository 边界情况测试"""

    @pytest.fixture
    def term_repo(self, mock_session):
        with patch.object(TermRepository, '__init__', lambda self, session: None):
            repo = TermRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.fixture
    def concept_repo(self, mock_session):
        with patch.object(ConceptRepository, '__init__', lambda self, session: None):
            repo = ConceptRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_domain_with_locked(self, term_repo, mock_session):
        mock_terms = [MagicMock()]
        with patch.object(term_repo, 'find_all', return_value=mock_terms):
            result = await term_repo.get_by_domain("science", locked=True)
            assert result == mock_terms

    @pytest.mark.asyncio
    async def test_find_similar_terms_no_synonyms(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = None
        mock_term.domain = "science"

        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_terms_with_synonyms_match(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = ["ai", "ml"]
        mock_term.domain = "science"

        mock_similar = MagicMock()
        mock_similar.id = uuid.uuid4()
        mock_similar.synonyms = ["ai", "deep learning"]
        mock_similar.domain = "science"

        # Set up mock_session.execute to return proper result
        mock_result = MockSelectResult(scalars_value=[mock_similar])
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_remove_synonym_not_found(self, term_repo, mock_session, sample_uuid):
        with patch.object(term_repo, 'get_by_id', return_value=None):
            result = await term_repo.remove_synonym(sample_uuid, "synonym")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_by_domain_with_locked_concept(self, concept_repo, mock_session):
        mock_concepts = [MagicMock()]
        with patch.object(concept_repo, 'find_all', return_value=mock_concepts):
            result = await concept_repo.get_by_domain("science", locked=True)
            assert result == mock_concepts


class TestAuditLogRepositoryEdgeCases:
    """AuditLogRepository 边界情况测试"""

    @pytest.fixture
    def audit_repo(self, mock_session):
        with patch.object(AuditLogRepository, '__init__', lambda self, session: None):
            repo = AuditLogRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_search_logs_with_resource_type(self, audit_repo, mock_session, sample_uuid):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.search_logs(resource_type="project")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_result(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.search_logs(result="success")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_until(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        from datetime import datetime
        until = datetime.utcnow()

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.search_logs(until=until)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_failed_actions_with_since(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=1)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.get_failed_actions(since=since)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_ip_address_with_since(self, audit_repo, mock_session):
        mock_logs = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_logs)
        mock_session.execute.return_value = mock_result

        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=24)

        with patch('db.repositories.audit_log_repository.select'):
            with patch('db.repositories.audit_log_repository.and_'):
                result = await audit_repo.get_by_ip_address("192.168.1.1", since=since)
                assert len(result) == 1


class TestKnowledgeGraphRepositoryEdgeCases:
    """KnowledgeGraphRepository 边界情况测试"""

    @pytest.fixture
    def kg_repo(self, mock_session):
        with patch.object(KnowledgeGraphRepository, '__init__', lambda self, session: None):
            repo = KnowledgeGraphRepository(mock_session)
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_edges_with_target_id(self, kg_repo, mock_session):
        mock_edges = [MagicMock()]
        mock_result = MockSelectResult(scalars_value=mock_edges)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            with patch('db.repositories.knowledge_graph_repository.and_'):
                result = await kg_repo.get_edges(target_id="node2")
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count_edges_with_type(self, kg_repo, mock_session):
        mock_result = MockSelectResult(scalar_value=15)
        mock_session.execute.return_value = mock_result

        with patch('db.repositories.knowledge_graph_repository.select'):
            result = await kg_repo.count_edges(edge_type="KNOWS")
            assert result == 15

    @pytest.mark.asyncio
    async def test_dfs_traverse_empty(self, kg_repo, mock_session):
        with patch.object(kg_repo, 'get_edges', return_value=[]):
            result = await kg_repo.dfs_traverse("node1")
            assert result == ["node1"]

    @pytest.mark.asyncio
    async def test_dfs_traverse_with_cycles(self, kg_repo, mock_session):
        mock_edge1 = MagicMock()
        mock_edge1.target_id = "node2"
        mock_edge2 = MagicMock()
        mock_edge2.source_id = "node3"

        call_count = [0]
        async def get_edges_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [mock_edge1]
            elif call_count[0] == 2:
                return []
            elif call_count[0] == 3:
                return [mock_edge2]
            return []

        with patch.object(kg_repo, 'get_edges', side_effect=get_edges_side_effect):
            result = await kg_repo.dfs_traverse("node1")
            assert "node1" in result


class TestChapterContentRepositoryEdgeCases:
    """ChapterContentRepository 边界情况测试"""

    @pytest.fixture
    def content_repo(self, mock_session):
        with patch.object(ChapterContentRepository, '__init__', lambda self, session: None):
            repo = ChapterContentRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo


class TestSectionRepositoryEdgeCases:
    """SectionRepository 边界情况测试"""

    @pytest.fixture
    def section_repo(self, mock_session):
        with patch.object(SectionRepository, '__init__', lambda self, session: None):
            repo = SectionRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_get_by_chapter_with_status(self, section_repo, mock_session, sample_uuid):
        mock_sections = [MagicMock()]
        with patch.object(section_repo, 'find_all', return_value=mock_sections):
            result = await section_repo.get_by_chapter(sample_uuid, status="published")
            assert result == mock_sections


class TestConceptRepositoryEdgeCases:
    """ConceptRepository 边界情况测试"""

    @pytest.fixture
    def concept_repo(self, mock_session):
        with patch.object(ConceptRepository, '__init__', lambda self, session: None):
            repo = ConceptRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_add_related_term_not_found(self, concept_repo, mock_session, sample_uuid):
        with patch.object(concept_repo, 'get_by_id', return_value=None):
            result = await concept_repo.add_related_term(sample_uuid, "new_term")
            assert result is None

    @pytest.mark.asyncio
    async def test_add_related_term_already_exists(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        mock_concept.related_terms = ["existing_term"]
        with patch.object(concept_repo, 'get_by_id', return_value=mock_concept):
            result = await concept_repo.add_related_term(sample_uuid, "existing_term")
            assert result == mock_concept

    @pytest.mark.asyncio
    async def test_remove_related_term_not_found(self, concept_repo, mock_session, sample_uuid):
        with patch.object(concept_repo, 'get_by_id', return_value=None):
            result = await concept_repo.remove_related_term(sample_uuid, "term")
            assert result is None

    @pytest.mark.asyncio
    async def test_remove_related_term_not_in_list(self, concept_repo, mock_session, sample_uuid):
        mock_concept = MagicMock()
        mock_concept.related_terms = ["existing"]
        with patch.object(concept_repo, 'get_by_id', return_value=mock_concept):
            result = await concept_repo.remove_related_term(sample_uuid, "not_existing")
            assert result == mock_concept


class TestRepositoryInitCoverage:
    """Test __init__ methods to achieve 100% coverage"""

    @pytest.fixture
    def mock_model(self):
        model = MagicMock()
        mock_id = MagicMock()
        mock_id.in_ = MagicMock(return_value=MagicMock())
        model.id = mock_id
        model.__table__ = MagicMock()
        model.__tablename__ = "mock_table"
        return model

    def test_base_repository_init(self, mock_session, mock_model):
        repo = BaseRepository(mock_model, mock_session)
        assert repo._model == mock_model
        assert repo._session == mock_session

    def test_user_repository_init(self, mock_session):
        repo = UserRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_role_repository_init(self, mock_session):
        repo = RoleRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_permission_repository_init(self, mock_session):
        repo = PermissionRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_project_repository_init(self, mock_session):
        repo = ProjectRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_project_member_repository_init(self, mock_session):
        repo = ProjectMemberRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_chapter_repository_init(self, mock_session):
        repo = ChapterRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_chapter_content_repository_init(self, mock_session):
        repo = ChapterContentRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_section_repository_init(self, mock_session):
        repo = SectionRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_term_repository_init(self, mock_session):
        repo = TermRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_concept_repository_init(self, mock_session):
        repo = ConceptRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_audit_log_repository_init(self, mock_session):
        repo = AuditLogRepository(mock_session)
        assert repo._model is not None
        assert repo._session == mock_session

    def test_knowledge_graph_repository_init(self, mock_session):
        repo = KnowledgeGraphRepository(mock_session)
        assert repo._session == mock_session


class TestTermRepositoryFindSimilarTerms:
    """Test find_similar_terms to cover lines 131, 146, 153-154"""

    @pytest.fixture
    def term_repo(self, mock_session):
        with patch.object(TermRepository, '__init__', lambda self, session: None):
            repo = TermRepository(mock_session)
            repo._model = MagicMock()
            repo._session = mock_session
            return repo

    @pytest.mark.asyncio
    async def test_find_similar_terms_term_not_found(self, term_repo, sample_uuid):
        with patch.object(term_repo, 'get_by_id', return_value=None):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_terms_no_synonyms(self, term_repo, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = []
        mock_term.domain = "test_domain"
        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            with patch.object(term_repo, 'find_all', return_value=[]):
                result = await term_repo.find_similar_terms(sample_uuid)
                assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_terms_with_self_in_list(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = ["syn1"]
        mock_term.domain = "test_domain"
        other_term = MagicMock()
        other_term.id = uuid.uuid4()  # Different id - SQL filtering handles this in real code
        other_term.synonyms = ["syn1"]
        other_term.domain = "other_domain"

        # Set up mock_session.execute to return proper result
        mock_result = MockSelectResult(scalars_value=[other_term])
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_similar_terms_same_domain_no_synonyms(self, term_repo, mock_session, sample_uuid):
        mock_term = MagicMock()
        mock_term.id = sample_uuid
        mock_term.synonyms = ["syn1"]
        mock_term.domain = "test_domain"
        other_term = MagicMock()
        other_term.id = uuid.uuid4()
        other_term.synonyms = []
        other_term.domain = "test_domain"

        # Set up mock_session.execute to return proper result
        mock_result = MockSelectResult(scalars_value=[other_term])
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(term_repo, 'get_by_id', return_value=mock_term):
            result = await term_repo.find_similar_terms(sample_uuid)
            assert other_term in result


class TestKnowledgeGraphRepositoryDfs:
    """Test dfs_traverse to cover line 331"""

    @pytest.fixture
    def kg_repo(self, mock_session):
        repo = KnowledgeGraphRepository(mock_session)
        return repo

    @pytest.mark.asyncio
    async def test_dfs_traverse_with_cycle(self, kg_repo, mock_session):
        node1 = MagicMock()
        node1.id = "node1"
        node1.node_type = "concept"
        node1.properties = {}
        node2 = MagicMock()
        node2.id = "node2"
        node2.node_type = "concept"
        node2.properties = {}

        async def mock_get_edges(source_id=None, target_id=None):
            if source_id == "node1":
                edge = MagicMock()
                edge.source_id = "node1"
                edge.target_id = "node2"
                edge.edge_type = "related"
                return [edge]
            elif target_id == "node1":
                edge = MagicMock()
                edge.source_id = "node2"
                edge.target_id = "node1"
                edge.edge_type = "related"
                return [edge]
            return []

        with patch.object(kg_repo, 'get_edges', side_effect=mock_get_edges):
            result = await kg_repo.dfs_traverse("node1")
            assert "node1" in result
            assert "node2" in result
