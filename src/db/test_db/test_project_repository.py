"""Tests for ProjectRepository."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockProject:
    """Mock Project model."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockProjectMember:
    """Mock ProjectMember model."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestProjectRepository:
    """Test ProjectRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = MagicMock()
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
    async def test_get_with_owner(self, mock_session, mock_result):
        """Test get_with_owner returns project with owner."""
        from db.repositories.project_repository import ProjectRepository

        mock_project = MagicMock()

        with patch.object(ProjectRepository, 'get_with_owner', return_value=mock_project):
            repo = ProjectRepository(mock_session)
            result = await repo.get_with_owner(uuid.uuid4())

            assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_with_members(self, mock_session, mock_result):
        """Test get_with_members returns project with members."""
        from db.repositories.project_repository import ProjectRepository

        mock_project = MagicMock()

        with patch.object(ProjectRepository, 'get_with_members', return_value=mock_project):
            repo = ProjectRepository(mock_session)
            result = await repo.get_with_members(uuid.uuid4())

            assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_with_chapters(self, mock_session, mock_result):
        """Test get_with_chapters returns project with chapters."""
        from db.repositories.project_repository import ProjectRepository

        mock_project = MagicMock()

        with patch.object(ProjectRepository, 'get_with_chapters', return_value=mock_project):
            repo = ProjectRepository(mock_session)
            result = await repo.get_with_chapters(uuid.uuid4())

            assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_full_project(self, mock_session, mock_result):
        """Test get_full_project returns complete project."""
        from db.repositories.project_repository import ProjectRepository

        mock_project = MagicMock()

        with patch.object(ProjectRepository, 'get_full_project', return_value=mock_project):
            repo = ProjectRepository(mock_session)
            result = await repo.get_full_project(uuid.uuid4())

            assert result == mock_project

    @pytest.mark.asyncio
    async def test_get_by_owner(self, mock_session):
        """Test get_by_owner calls find_all with owner filter."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        owner_id = uuid.uuid4()

        with patch.object(repo, "find_all", return_value=[]) as mock_find:
            await repo.get_by_owner(owner_id)

            mock_find.assert_called_once()
            call_kwargs = mock_find.call_args[1]
            assert call_kwargs["filters"] == {"owner_id": owner_id}

    @pytest.mark.asyncio
    async def test_get_by_owner_with_status(self, mock_session):
        """Test get_by_owner with status filter."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        owner_id = uuid.uuid4()

        with patch.object(repo, "find_all", return_value=[]) as mock_find:
            await repo.get_by_owner(owner_id, status="active")

            mock_find.assert_called_once()
            call_kwargs = mock_find.call_args[1]
            assert call_kwargs["filters"]["owner_id"] == owner_id
            assert call_kwargs["filters"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_by_status(self, mock_session):
        """Test get_by_status calls find_all with status filter."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)

        with patch.object(repo, "find_all", return_value=[]) as mock_find:
            await repo.get_by_status("active")

            mock_find.assert_called_once()
            call_kwargs = mock_find.call_args[1]
            assert call_kwargs["filters"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_project(self, mock_session):
        """Test create_project creates project with correct params."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        owner_id = uuid.uuid4()

        with patch.object(repo, "create", return_value=MockProject(id="123")) as mock_create:
            result = await repo.create_project(
                name="Test Project",
                owner_id=owner_id,
                description="Test description"
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["name"] == "Test Project"
            assert call_kwargs["owner_id"] == owner_id
            assert call_kwargs["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_update_progress(self, mock_session):
        """Test update_progress calls update with progress."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        with patch.object(repo, "update", return_value=MockProject(id=project_id)) as mock_update:
            await repo.update_progress(project_id, 50)

            mock_update.assert_called_once_with(project_id, current_progress=50)

    @pytest.mark.asyncio
    async def test_update_status(self, mock_session):
        """Test update_status calls update with status."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        with patch.object(repo, "update", return_value=MockProject(id=project_id)) as mock_update:
            await repo.update_status(project_id, "completed")

            mock_update.assert_called_once_with(project_id, status="completed")

    @pytest.mark.asyncio
    async def test_search_by_name(self, mock_session, mock_result):
        """Test search_by_name returns matching projects."""
        from db.repositories.project_repository import ProjectRepository

        mock_projects = [MagicMock()]

        with patch.object(ProjectRepository, 'search_by_name', return_value=mock_projects):
            repo = ProjectRepository(mock_session)
            result = await repo.search_by_name("test")

            assert len(result) == 1


class TestProjectMemberRepository:
    """Test ProjectMemberRepository methods."""

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
        result.scalar_one_or_none = MagicMock()
        result.scalars = MagicMock()
        result.scalars.return_value.all = MagicMock(return_value=[])
        return result

    @pytest.mark.asyncio
    async def test_get_members_of_project(self, mock_session, mock_result):
        """Test get_members_of_project returns members."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_members = [MagicMock()]

        with patch.object(ProjectMemberRepository, 'get_members_of_project', return_value=mock_members):
            repo = ProjectMemberRepository(mock_session)
            result = await repo.get_members_of_project(uuid.uuid4())

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_projects_of_user(self, mock_session, mock_result):
        """Test get_projects_of_user returns projects."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_project_members = [MagicMock()]

        with patch.object(ProjectMemberRepository, 'get_projects_of_user', return_value=mock_project_members):
            repo = ProjectMemberRepository(mock_session)
            result = await repo.get_projects_of_user(uuid.uuid4())

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_add_member(self, mock_session):
        """Test add_member creates member."""
        from db.repositories.project_repository import ProjectMemberRepository

        repo = ProjectMemberRepository(mock_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        with patch.object(repo, "create", return_value=MockProjectMember(id="123")) as mock_create:
            result = await repo.add_member(project_id, user_id, "editor")

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["project_id"] == project_id
            assert call_kwargs["user_id"] == user_id
            assert call_kwargs["role"] == "editor"

    @pytest.mark.asyncio
    async def test_is_member(self, mock_session):
        """Test is_member calls exists."""
        from db.repositories.project_repository import ProjectMemberRepository

        repo = ProjectMemberRepository(mock_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        with patch.object(repo, "exists", return_value=True) as mock_exists:
            result = await repo.is_member(project_id, user_id)

            mock_exists.assert_called_once_with(project_id=project_id, user_id=user_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_increment_chapter_count(self, mock_session):
        """Test increment_chapter_count increments total_chapters."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        mock_project = MockProject(id=project_id, total_chapters=3)

        with patch.object(repo, "get_by_id", return_value=mock_project) as mock_get:
            with patch.object(repo, "update", return_value=mock_project) as mock_update:
                result = await repo.increment_chapter_count(project_id)

                mock_get.assert_called_once_with(project_id)
                mock_update.assert_called_once_with(project_id, total_chapters=4)

    @pytest.mark.asyncio
    async def test_increment_chapter_count_not_found(self, mock_session):
        """Test increment_chapter_count returns None when project not found."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        with patch.object(repo, "get_by_id", return_value=None) as mock_get:
            result = await repo.increment_chapter_count(project_id)

            mock_get.assert_called_once_with(project_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_decrement_chapter_count(self, mock_session):
        """Test decrement_chapter_count decrements total_chapters."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        mock_project = MockProject(id=project_id, total_chapters=3)

        with patch.object(repo, "get_by_id", return_value=mock_project) as mock_get:
            with patch.object(repo, "update", return_value=mock_project) as mock_update:
                result = await repo.decrement_chapter_count(project_id)

                mock_get.assert_called_once_with(project_id)
                mock_update.assert_called_once_with(project_id, total_chapters=2)

    @pytest.mark.asyncio
    async def test_decrement_chapter_count_zero(self, mock_session):
        """Test decrement_chapter_count does not go below zero."""
        from db.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(mock_session)
        project_id = uuid.uuid4()

        mock_project = MockProject(id=project_id, total_chapters=0)

        with patch.object(repo, "get_by_id", return_value=mock_project) as mock_get:
            result = await repo.decrement_chapter_count(project_id)

            mock_get.assert_called_once_with(project_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_member_role(self, mock_session, mock_result):
        """Test get_member_role returns role string from DB."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_result.scalar_one_or_none.return_value = "editor"
        mock_session.execute.return_value = mock_result

        repo = ProjectMemberRepository(mock_session)
        result = await repo.get_member_role(uuid.uuid4(), uuid.uuid4())

        assert result == "editor"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_member_role_not_found(self, mock_session, mock_result):
        """Test get_member_role returns None when not found."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ProjectMemberRepository(mock_session)
        result = await repo.get_member_role(uuid.uuid4(), uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_update_member_role(self, mock_session):
        """Test update_member_role updates and returns member."""
        from db.repositories.project_repository import ProjectMemberRepository

        repo = ProjectMemberRepository(mock_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_member = MagicMock()
        mock_member.project_id = project_id
        mock_member.user_id = user_id
        mock_member.role = "viewer"

        with patch.object(repo, "get_one", return_value=mock_member) as mock_get:
            await repo.update_member_role(project_id, user_id, "editor")

            mock_get.assert_called_once_with(project_id=project_id, user_id=user_id)
            assert mock_member.role == "editor"
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_member_role_not_found(self, mock_session):
        """Test update_member_role returns None when not found."""
        from db.repositories.project_repository import ProjectMemberRepository

        repo = ProjectMemberRepository(mock_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        with patch.object(repo, "get_one", return_value=None) as mock_get:
            result = await repo.update_member_role(project_id, user_id, "editor")

            mock_get.assert_called_once_with(project_id=project_id, user_id=user_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_remove_member(self, mock_session, mock_result):
        """Test remove_member deletes and returns True."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_member = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_member
        mock_session.execute.return_value = mock_result

        repo = ProjectMemberRepository(mock_session)
        result = await repo.remove_member(uuid.uuid4(), uuid.uuid4())

        assert result is True
        mock_session.delete.assert_called_once_with(mock_member)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_member_not_found(self, mock_session, mock_result):
        """Test remove_member returns False when not found."""
        from db.repositories.project_repository import ProjectMemberRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ProjectMemberRepository(mock_session)
        result = await repo.remove_member(uuid.uuid4(), uuid.uuid4())

        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.flush.assert_not_called()



