"""
Term Schemas
"""

from pydantic import BaseModel, Field

# Search limit constants
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 100

# Term field length constraints
TERM_MIN_LENGTH = 1
TERM_MAX_LENGTH = 200
DEFINITION_MIN_LENGTH = 1
DOMAIN_MAX_LENGTH = 100


class TermCreate(BaseModel):
    """Term creation schema"""
    term: str = Field(..., min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: str = Field(..., min_length=DEFINITION_MIN_LENGTH)
    domain: str | None = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    synonyms: list[str] | None = Field(default_factory=list)
    first_defined_at: str | None = None


class TermUpdate(BaseModel):
    """Term update schema"""
    term: str | None = Field(default=None, min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: str | None = Field(default=None, min_length=DEFINITION_MIN_LENGTH)
    domain: str | None = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    synonyms: list[str] | None = None


class TermLockRequest(BaseModel):
    """Term lock request schema"""
    reason: str | None = Field(default=None, max_length=500)


class TermResponse(BaseModel):
    """Term response schema"""
    id: str
    term: str
    definition: str
    domain: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    locked: bool = False
    lock_reason: str | None = None
    version: int = Field(default=1, ge=1)
    first_defined_at: str | None = None
    usage_locations: list[str] = Field(default_factory=list)
    created_at: str


class TermSearchRequest(BaseModel):
    """Term search request schema"""
    query: str = Field(..., min_length=1, max_length=200)
    domain: str | None = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT)


class TermSearchResponse(BaseModel):
    """Term search response schema"""
    success: bool = True
    data: list[TermResponse]
    total: int = Field(default=0, ge=0)


class ConceptCreate(BaseModel):
    """Concept creation schema"""
    name: str = Field(..., min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: str = Field(..., min_length=DEFINITION_MIN_LENGTH)
    domain: str | None = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    related_terms: list[str] | None = None
    source_chapter_id: str | None = None


class LockTermRequest(BaseModel):
    """Request schema for locking a term"""
    reason: str | None = Field(default=None, max_length=500)


class ConceptUpdate(BaseModel):
    """Concept update schema"""
    name: str | None = Field(default=None, min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: str | None = Field(default=None, min_length=DEFINITION_MIN_LENGTH)
    domain: str | None = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    related_terms: list[str] | None = None
    locked: bool | None = None


class ConceptResponse(BaseModel):
    """Concept response schema"""
    id: str
    name: str
    definition: str
    domain: str | None = None
    related_terms: list[str] = Field(default_factory=list)
    source_chapter_id: str | None = None
    locked: bool = False
    created_at: str


class CitationCreate(BaseModel):
    """Citation creation schema"""
    chapter_id: str
    doi: str | None = Field(default=None, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    authors: list[str] | None = None
    journal: str | None = Field(default=None, max_length=255)
    year: int | None = Field(default=None, ge=1900, le=2100)
    url: str | None = Field(default=None, max_length=2000)


class CitationResponse(BaseModel):
    """Citation response schema"""
    id: str
    chapter_id: str
    doi: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    url: str | None = None
    verified: bool = False
    verified_at: str | None = None
    created_at: str
