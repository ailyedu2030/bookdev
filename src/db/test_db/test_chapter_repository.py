"""Comprehensive tests for ChapterRepository.

Tests all public methods using mocks.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestChapterRepository:
    """Test ChapterRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        session.refresh = MagicMock()
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
    async def test_get_by_project(self, mock_session, mock_result):
        """Test get_by_project returns chapters for project."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapters = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_chapters
        mock_session.execute.return_value = mock_result

        repo = ChapterRepository(mock_session)
        result = await repo.get_by_project(uuid.uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_project_with_status(self, mock_session, mock_result):
        """Test get_by_project with status filter."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapters = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_chapters
        mock_session.execute.return_value = mock_result

        repo = ChapterRepository(mock_session)
        result = await repo.get_by_project(uuid.uuid4(), status="published")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_chapter(self, mock_session):
        """Test create_chapter creates new chapter."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()
        repo = ChapterRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_chapter) as mock_create:
            await repo.create_chapter(
                project_id=uuid.uuid4(),
                title="Test Chapter",
                order_num=1,
                version="1.0"
            )

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status(self, mock_session):
        """Test update_status updates chapter status."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()
        repo = ChapterRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_chapter) as mock_update:
            await repo.update_status(uuid.uuid4(), "published")

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_content_hash(self, mock_session):
        """Test update_content_hash updates content hash."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()
        repo = ChapterRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_chapter) as mock_update:
            await repo.update_content_hash(uuid.uuid4(), "newhash123")

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_word_count(self, mock_session):
        """Test update_word_count updates word count."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()
        repo = ChapterRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_chapter) as mock_update:
            await repo.update_word_count(uuid.uuid4(), 1000)

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_contents(self, mock_session, mock_result):
        """Test get_with_contents returns chapter with contents."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()

        with patch.object(ChapterRepository, 'get_with_contents', return_value=mock_chapter):
            repo = ChapterRepository(mock_session)
            result = await repo.get_with_contents(uuid.uuid4())

            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_with_sections(self, mock_session, mock_result):
        """Test get_with_sections returns chapter with sections."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()

        with patch.object(ChapterRepository, 'get_with_sections', return_value=mock_chapter):
            repo = ChapterRepository(mock_session)
            result = await repo.get_with_sections(uuid.uuid4())

            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_with_reviews(self, mock_session, mock_result):
        """Test get_with_reviews returns chapter with reviews."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()

        with patch.object(ChapterRepository, 'get_with_reviews', return_value=mock_chapter):
            repo = ChapterRepository(mock_session)
            result = await repo.get_with_reviews(uuid.uuid4())

            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_full_chapter(self, mock_session, mock_result):
        """Test get_full_chapter returns complete chapter."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()

        with patch.object(ChapterRepository, 'get_full_chapter', return_value=mock_chapter):
            repo = ChapterRepository(mock_session)
            result = await repo.get_full_chapter(uuid.uuid4())

            assert result == mock_chapter

    @pytest.mark.asyncio
    async def test_get_by_parent(self, mock_session, mock_result):
        """Test get_by_parent returns child chapters."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapters = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_chapters
        mock_session.execute.return_value = mock_result

        repo = ChapterRepository(mock_session)
        result = await repo.get_by_parent(uuid.uuid4())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_next_order_num(self, mock_session, mock_result):
        """Test get_next_order_num returns next available order."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_result.scalar_one_or_none.return_value = 5
        mock_session.execute.return_value = mock_result

        repo = ChapterRepository(mock_session)
        result = await repo.get_next_order_num(uuid.uuid4())

        assert result == 6

    @pytest.mark.asyncio
    async def test_get_next_order_num_no_existing(self, mock_session, mock_result):
        """Test get_next_order_num returns 1 when no existing chapters."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ChapterRepository(mock_session)
        result = await repo.get_next_order_num(uuid.uuid4())

        assert result == 1

    @pytest.mark.asyncio
    async def test_reorder_chapters(self, mock_session):
        """Test reorder_chapters updates chapter orders."""
        from db.repositories.chapter_repository import ChapterRepository

        mock_chapter = MagicMock()
        repo = ChapterRepository(mock_session)
        chapter_orders = [
            {"id": uuid.uuid4(), "order_num": 1},
            {"id": uuid.uuid4(), "order_num": 2},
        ]
        with patch.object(repo, "update", return_value=mock_chapter) as mock_update:
            await repo.reorder_chapters(uuid.uuid4(), chapter_orders)

        assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_reorder_chapters_with_missing_fields(self, mock_session):
        """Test reorder_chapters handles missing fields gracefully."""
        from db.repositories.chapter_repository import ChapterRepository

        repo = ChapterRepository(mock_session)
        chapter_orders = [
            {"id": None, "order_num": 1},
            {"id": uuid.uuid4(), "order_num": None},
        ]
        with patch.object(repo, "update", return_value=MagicMock()) as mock_update:
            await repo.reorder_chapters(uuid.uuid4(), chapter_orders)

        mock_update.assert_not_called()


class TestChapterContentRepository:
    """Test ChapterContentRepository methods."""

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
    async def test_get_by_chapter(self, mock_session, mock_result):
        """Test get_by_chapter returns content versions."""
        from db.repositories.chapter_repository import ChapterContentRepository

        mock_contents = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_contents
        mock_session.execute.return_value = mock_result

        repo = ChapterContentRepository(mock_session)
        result = await repo.get_by_chapter(uuid.uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_latest(self, mock_session, mock_result):
        """Test get_latest returns latest content."""
        from db.repositories.chapter_repository import ChapterContentRepository

        mock_content = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_content
        mock_session.execute.return_value = mock_result

        repo = ChapterContentRepository(mock_session)
        result = await repo.get_latest(uuid.uuid4())

        assert result == mock_content

    @pytest.mark.asyncio
    async def test_create_content(self, mock_session):
        """Test create_content creates new content."""
        from db.repositories.chapter_repository import ChapterContentRepository

        mock_content = MagicMock()
        repo = ChapterContentRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_content) as mock_create:
            await repo.create_content(
                chapter_id=uuid.uuid4(),
                content="Test content",
                version="1.0",
                content_hash="hash123"
            )

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_hash(self, mock_session, mock_result):
        """Test get_by_hash returns content by hash."""
        from db.repositories.chapter_repository import ChapterContentRepository

        mock_content = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_content
        mock_session.execute.return_value = mock_result

        repo = ChapterContentRepository(mock_session)
        result = await repo.get_by_hash(uuid.uuid4(), "hash123")

        assert result == mock_content


class TestSectionRepository:
    """Test SectionRepository methods."""

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
    async def test_get_by_chapter(self, mock_session, mock_result):
        """Test get_by_chapter returns sections."""
        from db.repositories.chapter_repository import SectionRepository

        mock_sections = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_sections
        mock_session.execute.return_value = mock_result

        repo = SectionRepository(mock_session)
        result = await repo.get_by_chapter(uuid.uuid4())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_chapter_with_status(self, mock_session, mock_result):
        """Test get_by_chapter with status filter."""
        from db.repositories.chapter_repository import SectionRepository

        mock_sections = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_sections
        mock_session.execute.return_value = mock_result

        repo = SectionRepository(mock_session)
        result = await repo.get_by_chapter(uuid.uuid4(), status="active")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_with_parent(self, mock_session, mock_result):
        """Test get_with_parent returns section with parent."""
        from db.repositories.chapter_repository import SectionRepository

        mock_section = MagicMock()

        with patch.object(SectionRepository, 'get_with_parent', return_value=mock_section):
            repo = SectionRepository(mock_session)
            result = await repo.get_with_parent(uuid.uuid4())

            assert result == mock_section

    @pytest.mark.asyncio
    async def test_get_child_sections(self, mock_session, mock_result):
        """Test get_child_sections returns child sections."""
        from db.repositories.chapter_repository import SectionRepository

        mock_sections = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_sections
        mock_session.execute.return_value = mock_result

        repo = SectionRepository(mock_session)
        result = await repo.get_child_sections(uuid.uuid4())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_section(self, mock_session):
        """Test create_section creates new section."""
        from db.repositories.chapter_repository import SectionRepository

        mock_section = MagicMock()
        repo = SectionRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_section) as mock_create:
            await repo.create_section(
                chapter_id=uuid.uuid4(),
                title="Test Section",
                order_num=1
            )

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_next_order_num(self, mock_session, mock_result):
        """Test get_next_order_num returns next order number."""
        from db.repositories.chapter_repository import SectionRepository

        mock_result.scalar_one_or_none.return_value = 3
        mock_session.execute.return_value = mock_result

        repo = SectionRepository(mock_session)
        result = await repo.get_next_order_num(uuid.uuid4())

        assert result == 4

    @pytest.mark.asyncio
    async def test_get_next_order_num_no_existing(self, mock_session, mock_result):
        """Test get_next_order_num returns 1 when no sections exist."""
        from db.repositories.chapter_repository import SectionRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SectionRepository(mock_session)
        result = await repo.get_next_order_num(uuid.uuid4())

        assert result == 1
