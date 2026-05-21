"""Comprehensive tests for TermRepository and ConceptRepository.

Tests all public methods using mocks.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestTermRepository:
    """Test TermRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        session.refresh = AsyncMock()
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
    async def test_get_by_term(self, mock_session, mock_result):
        """Test get_by_term returns term when found."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.term = "test term"
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_by_term("test term")

        assert result == mock_term

    @pytest.mark.asyncio
    async def test_get_by_term_not_found(self, mock_session, mock_result):
        """Test get_by_term returns None when not found."""
        from db.repositories.term_repository import TermRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_by_term("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_domain(self, mock_session, mock_result):
        """Test get_by_domain returns terms in domain."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_by_domain("science")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_domain_with_locked(self, mock_session, mock_result):
        """Test get_by_domain with locked filter."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_by_domain("science", locked=True)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_term(self, mock_session):
        """Test create_term creates new term."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        repo = TermRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_term) as mock_create:
            await repo.create_term(
                term="new term",
                definition="definition",
                domain="science"
            )

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_term(self, mock_session, mock_result):
        """Test lock_term locks term."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        repo = TermRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_term) as mock_update:
            await repo.lock_term(uuid.uuid4())

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlock_term(self, mock_session, mock_result):
        """Test unlock_term unlocks term."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        repo = TermRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_term) as mock_update:
            await repo.unlock_term(uuid.uuid4())

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_locked_terms(self, mock_session, mock_result):
        """Test get_locked_terms returns locked terms."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_locked_terms()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_unlocked_terms(self, mock_session, mock_result):
        """Test get_unlocked_terms returns unlocked terms."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.get_unlocked_terms()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_term(self, mock_session, mock_result):
        """Test search_by_term returns matching terms."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.search_by_term("test")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_by_definition(self, mock_session, mock_result):
        """Test search_by_definition returns matching terms."""
        from db.repositories.term_repository import TermRepository

        mock_terms = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_terms
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        result = await repo.search_by_definition("definition query")

        assert len(result) == 1


class TestConceptRepository:
    """Test ConceptRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        session.refresh = AsyncMock()
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
        """Test get_by_name returns concept when found."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        mock_concept.name = "test concept"
        mock_result.scalar_one_or_none.return_value = mock_concept
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.get_by_name("test concept")

        assert result == mock_concept

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, mock_session, mock_result):
        """Test get_by_name returns None when not found."""
        from db.repositories.term_repository import ConceptRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.get_by_name("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_concept(self, mock_session):
        """Test create_concept creates new concept."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        repo = ConceptRepository(mock_session)
        with patch.object(repo, "create", return_value=mock_concept) as mock_create:
            await repo.create_concept(
                name="new concept",
                definition="description"
            )

        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_concept(self, mock_session, mock_result):
        """Test lock_concept locks concept."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        repo = ConceptRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_concept) as mock_update:
            await repo.lock_concept(uuid.uuid4())

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlock_concept(self, mock_session, mock_result):
        """Test unlock_concept unlocks concept."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        repo = ConceptRepository(mock_session)
        with patch.object(repo, "update", return_value=mock_concept) as mock_update:
            await repo.unlock_concept(uuid.uuid4())

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_locked_concepts(self, mock_session, mock_result):
        """Test get_locked_concepts returns locked concepts."""
        from db.repositories.term_repository import ConceptRepository

        mock_concepts = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_concepts
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.get_locked_concepts()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_unlocked_concepts(self, mock_session, mock_result):
        """Test get_unlocked_concepts returns unlocked concepts."""
        from db.repositories.term_repository import ConceptRepository

        mock_concepts = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_concepts
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.get_unlocked_concepts()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_name(self, mock_session, mock_result):
        """Test search_by_name returns matching concepts."""
        from db.repositories.term_repository import ConceptRepository

        mock_concepts = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_concepts
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.search_by_name("test")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_by_definition(self, mock_session, mock_result):
        """Test search_by_definition returns matching concepts."""
        from db.repositories.term_repository import ConceptRepository

        mock_concepts = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_concepts
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.search_by_definition("definition query")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_source_chapter(self, mock_session, mock_result):
        """Test get_by_source_chapter returns concepts from chapter."""
        from db.repositories.term_repository import ConceptRepository

        mock_concepts = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_concepts
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        result = await repo.get_by_source_chapter(uuid.uuid4())

        assert len(result) == 1


class TestTermRepositorySynonymOperations:
    """Test TermRepository synonym operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
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
    async def test_add_synonym(self, mock_session, mock_result):
        """Test add_synonym adds synonym to term."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.synonyms = ["old_synonym"]
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_term):
            await repo.add_synonym(uuid.uuid4(), "new_synonym")

        assert "new_synonym" in mock_term.synonyms
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_add_synonym_term_not_found(self, mock_session, mock_result):
        """Test add_synonym returns None when term not found."""
        from db.repositories.term_repository import TermRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.add_synonym(uuid.uuid4(), "synonym")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_synonym_already_exists(self, mock_session, mock_result):
        """Test add_synonym does not add duplicate."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.synonyms = ["existing"]
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_term):
            await repo.add_synonym(uuid.uuid4(), "existing")

        assert mock_session.flush.call_count == 0

    @pytest.mark.asyncio
    async def test_remove_synonym(self, mock_session, mock_result):
        """Test remove_synonym removes synonym from term."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.synonyms = ["to_remove", "to_keep"]
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_term):
            await repo.remove_synonym(uuid.uuid4(), "to_remove")

        assert "to_remove" not in mock_term.synonyms
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_remove_synonym_not_found(self, mock_session, mock_result):
        """Test remove_synonym returns None when term not found."""
        from db.repositories.term_repository import TermRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.remove_synonym(uuid.uuid4(), "synonym")

        assert result is None

    @pytest.mark.asyncio
    async def test_remove_synonym_not_in_list(self, mock_session, mock_result):
        """Test remove_synonym does nothing when synonym not in list."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.synonyms = ["other"]
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_term):
            await repo.remove_synonym(uuid.uuid4(), "nonexistent")

        assert mock_session.flush.call_count == 0


class TestTermRepositoryFindSimilarTerms:
    """Test TermRepository.find_similar_terms method."""

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
    async def test_find_similar_terms_no_term(self, mock_session, mock_result):
        """Test find_similar_terms returns empty when term not found."""
        from db.repositories.term_repository import TermRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.find_similar_terms(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_terms_no_synonyms(self, mock_session, mock_result):
        """Test find_similar_terms returns empty when term has no synonyms."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.synonyms = None
        mock_result.scalar_one_or_none.return_value = mock_term
        mock_session.execute.return_value = mock_result

        repo = TermRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_term):
            result = await repo.find_similar_terms(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_terms_with_matching_synonyms(self, mock_session, mock_result):
        """Test find_similar_terms finds terms with matching synonyms."""
        from db.repositories.term_repository import TermRepository

        mock_term = MagicMock()
        mock_term.id = uuid.uuid4()
        mock_term.synonyms = ["ai", "machine learning"]
        mock_term.domain = "tech"

        mock_other_term = MagicMock()
        mock_other_term.id = uuid.uuid4()
        mock_other_term.synonyms = ["ai", "artificial intelligence"]
        mock_other_term.domain = "tech"

        with patch.object(TermRepository, "get_by_id", return_value=mock_term):
            with patch.object(TermRepository, "find_all", return_value=[mock_term, mock_other_term]):
                repo = TermRepository(mock_session)
                result = await repo.find_similar_terms(mock_term.id)

        assert mock_other_term in result


class TestConceptRepositoryRelatedTerms:
    """Test ConceptRepository related terms operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
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
    async def test_add_related_term(self, mock_session, mock_result):
        """Test add_related_term adds term to concept."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        mock_concept.related_terms = ["existing"]
        mock_result.scalar_one_or_none.return_value = mock_concept
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_concept):
            await repo.add_related_term(uuid.uuid4(), "new_term")

        assert "new_term" in mock_concept.related_terms
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_add_related_term_concept_not_found(self, mock_session, mock_result):
        """Test add_related_term returns None when concept not found."""
        from db.repositories.term_repository import ConceptRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.add_related_term(uuid.uuid4(), "term")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_related_term_already_exists(self, mock_session, mock_result):
        """Test add_related_term does not add duplicate."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        mock_concept.related_terms = ["existing"]
        mock_result.scalar_one_or_none.return_value = mock_concept
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_concept):
            await repo.add_related_term(uuid.uuid4(), "existing")

        assert mock_session.flush.call_count == 0

    @pytest.mark.asyncio
    async def test_remove_related_term(self, mock_session, mock_result):
        """Test remove_related_term removes term from concept."""
        from db.repositories.term_repository import ConceptRepository

        mock_concept = MagicMock()
        mock_concept.related_terms = ["to_remove", "to_keep"]
        mock_result.scalar_one_or_none.return_value = mock_concept
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=mock_concept):
            await repo.remove_related_term(uuid.uuid4(), "to_remove")

        assert "to_remove" not in mock_concept.related_terms
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_remove_related_term_not_found(self, mock_session, mock_result):
        """Test remove_related_term returns None when concept not found."""
        from db.repositories.term_repository import ConceptRepository

        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = ConceptRepository(mock_session)
        with patch.object(repo, "get_by_id", return_value=None):
            result = await repo.remove_related_term(uuid.uuid4(), "term")

        assert result is None



