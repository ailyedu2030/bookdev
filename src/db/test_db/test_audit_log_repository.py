"""Comprehensive tests for AuditLogRepository.

Tests all public methods using mocks.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuditLogRepository:
    """Test AuditLogRepository methods."""

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
    async def test_get_by_user(self, mock_session, mock_result):
        """Test get_by_user returns user logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_by_user(uuid.uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_resource(self, mock_session, mock_result):
        """Test get_by_resource returns resource logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_by_resource("user", uuid.uuid4())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_event_type(self, mock_session, mock_result):
        """Test get_by_event_type returns matching logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_by_event_type("login")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_event_type_with_since(self, mock_session, mock_result):
        """Test get_by_event_type with since filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(hours=1)
        result = await repo.get_by_event_type("login", since=since)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recent_logs(self, mock_session, mock_result):
        """Test get_recent_logs returns recent logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock(), MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_recent_logs(hours=24)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_search_logs_no_filters(self, mock_session, mock_result):
        """Test search_logs with no filters."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.search_logs()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_event_type(self, mock_session, mock_result):
        """Test search_logs with event_type filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.search_logs(event_type="login")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_multiple_filters(self, mock_session, mock_result):
        """Test search_logs with multiple filters."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.search_logs(
            event_type="login", user_id=uuid.uuid4(), action="authenticate", result="success"
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_date_range(self, mock_session, mock_result):
        """Test search_logs with date range."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(days=1)
        until = datetime.utcnow()
        result = await repo.search_logs(since=since, until=until)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logs_with_resource_type(self, mock_session, mock_result):
        """Test search_logs with resource_type filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.search_logs(resource_type="project")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_log(self, mock_session):
        """Test create_log creates new log."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_log = MagicMock()
        repo = AuditLogRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_log) as mock_create:
            await repo.create_log(event_type="login", action="authenticate", result="success")

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_event_type(self, mock_session, mock_result):
        """Test count_by_event_type returns count."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.count_by_event_type("login")

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_event_type_with_since(self, mock_session, mock_result):
        """Test count_by_event_type with since filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(hours=1)
        result = await repo.count_by_event_type("login", since=since)

        assert result == 3

    @pytest.mark.asyncio
    async def test_count_by_user(self, mock_session, mock_result):
        """Test count_by_user returns count."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.count_by_user(uuid.uuid4())

        assert result == 10

    @pytest.mark.asyncio
    async def test_count_by_user_with_since(self, mock_session, mock_result):
        """Test count_by_user with since filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one.return_value = 2
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(days=7)
        result = await repo.count_by_user(uuid.uuid4(), since=since)

        assert result == 2

    @pytest.mark.asyncio
    async def test_get_failed_actions(self, mock_session, mock_result):
        """Test get_failed_actions returns failed logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_failed_actions()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_failed_actions_with_since(self, mock_session, mock_result):
        """Test get_failed_actions with since filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(hours=1)
        result = await repo.get_failed_actions(since=since)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_ip_address(self, mock_session, mock_result):
        """Test get_by_ip_address returns matching logs."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.get_by_ip_address("192.168.1.1")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_ip_address_with_since(self, mock_session, mock_result):
        """Test get_by_ip_address with since filter."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_logs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        since = datetime.utcnow() - timedelta(days=1)
        result = await repo.get_by_ip_address("192.168.1.1", since=since)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_verify_signature_valid(self, mock_session, mock_result):
        """Test verify_signature returns True for valid signature."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one_or_none.return_value = "valid_signature"
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.verify_signature(uuid.uuid4(), "valid_signature")

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid(self, mock_session, mock_result):
        """Test verify_signature returns False for invalid signature."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one_or_none.return_value = "stored_signature"
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.verify_signature(uuid.uuid4(), "wrong_signature")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_signature_not_found(self, mock_session, mock_result):
        """Test verify_signature returns False when log not found."""
        from db.repositories.audit_log_repository import AuditLogRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = AuditLogRepository(mock_session)
        result = await repo.verify_signature(uuid.uuid4(), "any_signature")

        assert result is False
