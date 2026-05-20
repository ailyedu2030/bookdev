"""
Term Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TermCreate(BaseModel):
    """Term creation schema"""
    term: str = Field(..., min_length=1, max_length=200)
    definition: str = Field(..., min_length=1)
    domain: Optional[str] = Field(default=None, max_length=100)
    synonyms: Optional[List[str]] = Field(default_factory=list)
    first_defined_at: Optional[str] = None


class TermUpdate(BaseModel):
    """Term update schema"""
    term: Optional[str] = Field(default=None, min_length=1, max_length=200)
    definition: Optional[str] = Field(default=None, min_length=1)
    domain: Optional[str] = Field(default=None, max_length=100)
    synonyms: Optional[List[str]] = None


class TermLockRequest(BaseModel):
    """Term lock request schema"""
    reason: Optional[str] = None


class TermResponse(BaseModel):
    """Term response schema"""
    id: str
    term: str
    definition: str
    domain: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    locked: bool = False
    version: int = 1
    first_defined_at: Optional[str] = None
    usage_locations: List[str] = Field(default_factory=list)
    created_at: str


class TermSearchRequest(BaseModel):
    """Term search request schema"""
    query: str = Field(..., min_length=1)
    domain: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class TermSearchResponse(BaseModel):
    """Term search response schema"""
    success: bool = True
    data: List[TermResponse]
    total: int


class ConceptCreate(BaseModel):
    """Concept creation schema"""
    name: str = Field(..., min_length=1, max_length=200)
    definition: str = Field(..., min_length=1)
    domain: Optional[str] = Field(default=None, max_length=100)
    related_terms: Optional[List[str]] = None
    source_chapter_id: Optional[str] = None


class ConceptUpdate(BaseModel):
    """Concept update schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    definition: Optional[str] = Field(default=None, min_length=1)
    domain: Optional[str] = Field(default=None, max_length=100)
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
    doi: Optional[str] = None
    title: str
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None


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
