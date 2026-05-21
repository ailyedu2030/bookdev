"""
Term Schemas
"""

from datetime import datetime, timezone
from typing import Optional, List, Literal
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
    domain: Optional[str] = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    synonyms: Optional[List[str]] = Field(default_factory=list)
    first_defined_at: Optional[str] = None


class TermUpdate(BaseModel):
    """Term update schema"""
    term: Optional[str] = Field(default=None, min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: Optional[str] = Field(default=None, min_length=DEFINITION_MIN_LENGTH)
    domain: Optional[str] = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    synonyms: Optional[List[str]] = None


class TermLockRequest(BaseModel):
    """Term lock request schema"""
    reason: Optional[str] = Field(default=None, max_length=500)


class TermResponse(BaseModel):
    """Term response schema"""
    id: str
    term: str
    definition: str
    domain: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    locked: bool = False
    lock_reason: Optional[str] = None
    version: int = Field(default=1, ge=1)
    first_defined_at: Optional[str] = None
    usage_locations: List[str] = Field(default_factory=list)
    created_at: str


class TermSearchRequest(BaseModel):
    """Term search request schema"""
    query: str = Field(..., min_length=1, max_length=200)
    domain: Optional[str] = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT)


class TermSearchResponse(BaseModel):
    """Term search response schema"""
    success: bool = True
    data: List[TermResponse]
    total: int = Field(default=0, ge=0)


class ConceptCreate(BaseModel):
    """Concept creation schema"""
    name: str = Field(..., min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: str = Field(..., min_length=DEFINITION_MIN_LENGTH)
    domain: Optional[str] = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    related_terms: Optional[List[str]] = None
    source_chapter_id: Optional[str] = None


class LockTermRequest(BaseModel):
    """Request schema for locking a term"""
    reason: Optional[str] = Field(default=None, max_length=500)


class ConceptUpdate(BaseModel):
    """Concept update schema"""
    name: Optional[str] = Field(default=None, min_length=TERM_MIN_LENGTH, max_length=TERM_MAX_LENGTH)
    definition: Optional[str] = Field(default=None, min_length=DEFINITION_MIN_LENGTH)
    domain: Optional[str] = Field(default=None, max_length=DOMAIN_MAX_LENGTH)
    related_terms: Optional[List[str]] = None
    locked: Optional[bool] = None


class ConceptResponse(BaseModel):
    """Concept response schema"""
    id: str
    name: str
    definition: str
    domain: Optional[str] = None
    related_terms: List[str] = Field(default_factory=list)
    source_chapter_id: Optional[str] = None
    locked: bool = False
    created_at: str


class CitationCreate(BaseModel):
    """Citation creation schema"""
    chapter_id: str
    doi: Optional[str] = Field(default=None, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    authors: Optional[List[str]] = None
    journal: Optional[str] = Field(default=None, max_length=255)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    url: Optional[str] = Field(default=None, max_length=2000)


class CitationResponse(BaseModel):
    """Citation response schema"""
    id: str
    chapter_id: str
    doi: Optional[str] = None
    title: str
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    verified: bool = False
    verified_at: Optional[str] = None
    created_at: str
