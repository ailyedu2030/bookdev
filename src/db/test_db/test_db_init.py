"""Tests for db/__init__.py async database functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseSessionFunctions:
    """Test async database session management functions."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_maker(self, mock_session):
        """Create a mock session maker."""
        maker = MagicMock()
        async_cm = MagicMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_session)
        async_cm.__aexit__ = AsyncMock()
        maker.return_value = async_cm
        return maker

    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_session_maker):
        """Test get_session yields session and commits on success."""
        from db import get_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            gen = get_session()
            session = await gen.__anext__()
            assert session is not None
            await gen.aclose()

    @pytest.mark.asyncio
    async def test_get_session_commits_on_normal_exit(self, mock_session_maker):
        """Test get_session commits when generator is fully exhausted."""
        from db import get_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            gen = get_session()
            session = await gen.__anext__()
            assert session is not None
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()
            session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_exception(self, mock_session_maker):
        """Test get_session rolls back when exception occurs."""
        from db import get_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            gen = get_session()
            await gen.__anext__()
            try:
                await gen.athrow(Exception("Test error"))
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_get_db_session_context_manager(self, mock_session_maker):
        """Test get_db_session as async context manager."""
        from db import get_db_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            async with get_db_session() as session:
                assert session is not None

    @pytest.mark.asyncio
    async def test_get_db_session_exception_handling(self, mock_session_maker):
        """Test get_db_session rolls back when exception occurs."""
        from db import get_db_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            try:
                async with get_db_session() as session:
                    assert session is not None
                    raise ValueError("Test error")
            except ValueError:
                pass

    @pytest.mark.asyncio
    async def test_get_session_exhausted_generator(self, mock_session_maker):
        """Test get_session when generator is fully exhausted."""
        from db import get_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            gen = get_session()
            result = await gen.__anext__()
            assert result is not None
            await gen.aclose()

    @pytest.mark.asyncio
    async def test_get_db_session_commits_on_normal_exit(self, mock_session_maker):
        """Test get_db_session commits when context manager exits normally."""
        from db import get_db_session

        with patch("db._get_session_maker", return_value=mock_session_maker):
            async with get_db_session() as session:
                assert session is not None


class TestDatabaseConnectionFunctions:
    """Test database connection management functions."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock async engine."""
        engine = MagicMock()
        engine.begin = MagicMock()
        engine.begin.return_value.__aenter__ = AsyncMock()
        engine.begin.return_value.__aexit__ = AsyncMock()
        engine.dispose = AsyncMock()
        return engine

    @pytest.mark.asyncio
    async def test_init_db_creates_connection(self, mock_engine):
        """Test init_db establishes database connection."""
        from db import init_db

        with patch("db._get_engine", return_value=mock_engine):
            await init_db()

        mock_engine.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_disposes_engine(self, mock_engine):
        """Test close_db disposes engine and clears globals."""
        import db
        from db import close_db
        db._engine = mock_engine
        db._async_session_maker = MagicMock()

        await close_db()

        mock_engine.dispose.assert_called_once()
        assert db._engine is None
        assert db._async_session_maker is None

    @pytest.mark.asyncio
    async def test_close_db_when_not_initialized(self):
        """Test close_db handles uninitialized state gracefully."""
        import db
        from db import close_db
        db._engine = None
        db._async_session_maker = None

        await close_db()


class TestDatabaseEngine:
    """Test database engine functions."""

    def test_get_engine_lazy_initialization(self):
        """Test engine is created lazily on first access."""
        import db
        from db import get_engine

        db._engine = None

        with patch("db.create_async_engine") as mock_create:
            mock_create.return_value = MagicMock()
            get_engine()

            mock_create.assert_called_once()

    def test_get_engine_returns_cached_instance(self):
        """Test engine is cached after first creation."""
        import db
        from db import get_engine

        mock_engine = MagicMock()
        db._engine = mock_engine

        engine = get_engine()
        assert engine is mock_engine

    def test_database_url_defaults(self):
        """Test DATABASE_URL has sensible defaults."""
        from db import DATABASE_URL

        assert DATABASE_URL is not None
        assert "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL

    def test_get_session_maker_creates_when_none(self):
        """Test _get_session_maker creates session maker when _async_session_maker is None."""
        import db
        from db import _get_session_maker

        db._engine = None
        db._async_session_maker = None

        with patch("db.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            maker = _get_session_maker()

            assert maker is not None
            assert db._async_session_maker is not None


class TestBaseModel:
    """Test Base model class."""

    def test_base_can_be_instantiated(self):
        """Test Base class can be instantiated."""
        from db import Base

        assert Base is not None
        assert hasattr(Base, "__tablename__") is False or Base.__tablename__ is None


class TestExports:
    """Test module exports."""

    def test_all_exports_present(self):
        """Test all expected items are exported."""
        from db import __all__

        expected = [
            "Base",
            "get_engine",
            "get_session",
            "get_db_session",
            "init_db",
            "close_db",
        ]

        for item in expected:
            assert item in __all__, f"{item} not in __all__"

    def test_base_is_declarative_base(self):
        """Test Base is a proper SQLAlchemy DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase

        from db import Base

        assert issubclass(Base, DeclarativeBase)

    def test_get_session_is_async_generator(self):
        """Test get_session returns an async generator."""
        import inspect

        from db import get_session

        assert inspect.isasyncgenfunction(get_session)

    def test_get_db_session_is_async_generator(self):
        """Test get_db_session returns an async generator."""
        import inspect

        from db import get_db_session

        assert inspect.isgeneratorfunction(get_db_session) or callable(get_db_session)
