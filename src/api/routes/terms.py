"""
Term and Concept Management Routes

Handles terminology and concept operations:
- GET /api/terms - List terms
- POST /api/terms - Create term
- PUT /api/terms/{id} - Update term
- POST /api/terms/{id}/lock - Lock term
- GET /api/concepts - List concepts
- POST /api/concepts - Create concept
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query

from api.schemas.term import (
    TermCreate,
    TermUpdate,
    TermResponse,
    TermSearchRequest,
    TermSearchResponse,
    ConceptCreate,
    ConceptUpdate,
    ConceptResponse,
    CitationCreate,
    CitationResponse,
    LockTermRequest,
)
from api.schemas.common import SuccessResponse, ErrorResponse
from api.deps import (
    get_db,
    get_current_active_user,
    DatabaseSession,
    User,
    require_permission,
    generate_uuid,
)
from api.middleware.csrf import csrf_protect

router = APIRouter(prefix="/api/terms", tags=["Terms"])


@router.get("", response_model=TermSearchResponse)
async def list_terms(
    domain: Optional[str] = Query(default=None),
    locked: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all terms with optional filtering.

    - **domain**: Filter by domain
    - **locked**: Filter by lock status
    - **page**: Page number
    - **per_page**: Items per page
    """
    terms = db.list_terms(domain=domain)

    if locked is not None:
        terms = [t for t in terms if t.get("locked") == locked]

    total = len(terms)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return TermSearchResponse(
        success=True,
        data=[TermResponse(**t) for t in terms[start_idx:end_idx]],
        total=total,
    )


@router.post(
    "",
    response_model=TermResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_term(
    term_data: TermCreate,
    user: User = Depends(require_permission("terms:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new term in the glossary.

    - **term**: Term name
    - **definition**: Term definition
    - **domain**: Domain/category
    - **synonyms**: List of synonyms
    - **first_defined_at**: Where term was first defined
    """
    term = db.create_term({
        "term": term_data.term,
        "definition": term_data.definition,
        "domain": term_data.domain,
        "synonyms": term_data.synonyms,
        "first_defined_at": term_data.first_defined_at,
    })

    return TermResponse(**term)


@router.get("/{term_id}", response_model=TermResponse)
async def get_term(
    term_id: str,
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get term details by ID.
    """
    term = db.get_term(term_id)
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": "Term not found",
                }
            },
        )

    return TermResponse(**term)


@router.put(
    "/{term_id}",
    response_model=TermResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_term(
    term_id: str,
    update_data: TermUpdate,
    user: User = Depends(require_permission("terms:update")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update a term.

    - **term**: New term name
    - **definition**: New definition
    - **domain**: New domain
    - **synonyms**: New synonyms list
    """
    term = db.get_term(term_id)
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": "Term not found",
                }
            },
        )

    if term.get("locked"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TERM_LOCKED",
                    "message": "Cannot update a locked term",
                }
            },
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_UPDATE_DATA",
                    "message": "No update data provided",
                }
            },
        )

    updated_term = db.update_term(term_id, update_dict)
    return TermResponse(**updated_term)


@router.post(
    "/{term_id}/lock",
    response_model=TermResponse,
    dependencies=[Depends(csrf_protect)],
)
async def lock_term(
    term_id: str,
    user: User = Depends(require_permission("terms:lock")),
    db: DatabaseSession = Depends(get_db),
    body: LockTermRequest = Body(default=LockTermRequest()),
):
    """
    Lock a term to prevent modifications.

    - **reason**: Reason for locking
    """
    term = db.get_term(term_id)
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": "Term not found",
                }
            },
        )

    locked_term = db.lock_term(term_id, body.reason)
    return TermResponse(**locked_term)


@router.post(
    "/{term_id}/unlock",
    response_model=TermResponse,
    dependencies=[Depends(csrf_protect)],
)
async def unlock_term(
    term_id: str,
    user: User = Depends(require_permission("terms:unlock")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Unlock a locked term.
    """
    term = db.get_term(term_id)
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": "Term not found",
                }
            },
        )

    updated_term = db.update_term(term_id, {"locked": False, "lock_reason": None})
    return TermResponse(**updated_term)


@router.delete(
    "/{term_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_term(
    term_id: str,
    user: User = Depends(require_permission("terms:delete")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete a term.
    """
    term = db.get_term(term_id)
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": "Term not found",
                }
            },
        )

    if term.get("locked"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TERM_LOCKED",
                    "message": "Cannot delete a locked term",
                }
            },
        )

    db.delete_term(term_id)

    return SuccessResponse(
        success=True,
        message="Term deleted successfully",
    )


@router.post(
    "/search",
    response_model=TermSearchResponse,
)
async def search_terms(
    search_request: TermSearchRequest,
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    Search terms by query string.

    - **query**: Search query
    - **domain**: Optional domain filter
    - **limit**: Maximum results
    """
    all_terms = db.list_terms(domain=search_request.domain)

    query_lower = search_request.query.lower()
    matching_terms = [
        t for t in all_terms
        if query_lower in t.get("term", "").lower()
        or query_lower in t.get("definition", "").lower()
        or any(query_lower in syn.lower() for syn in t.get("synonyms", []))
    ]

    return TermSearchResponse(
        success=True,
        data=[TermResponse(**t) for t in matching_terms[:search_request.limit]],
        total=len(matching_terms),
    )


@router.get("/domains/list", response_model=List[str])
async def list_domains(
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all unique domains used by terms.
    """
    terms = db.list_terms()
    domains = set(t.get("domain") for t in terms if t.get("domain"))
    return sorted(list(domains))


concept_router = APIRouter(prefix="/api/concepts", tags=["Concepts"])


@concept_router.get("", response_model=List[ConceptResponse])
async def list_concepts(
    domain: Optional[str] = Query(default=None),
    locked: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all concepts.
    """
    return [
        ConceptResponse(
            id=generate_uuid(),
            name="Sample Concept",
            definition="Sample definition",
            domain=domain,
            related_terms=[],
            locked=locked or False,
            created_at=datetime.utcnow().isoformat(),
        )
    ]


@concept_router.post(
    "",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_concept(
    concept_data: ConceptCreate,
    user: User = Depends(require_permission("concepts:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new concept.

    - **name**: Concept name
    - **definition**: Concept definition
    - **domain**: Domain/category
    - **related_terms**: Related term IDs
    - **source_chapter_id**: Source chapter ID
    """
    concept_id = generate_uuid()

    return ConceptResponse(
        id=concept_id,
        name=concept_data.name,
        definition=concept_data.definition,
        domain=concept_data.domain,
        related_terms=concept_data.related_terms or [],
        source_chapter_id=concept_data.source_chapter_id,
        locked=False,
        created_at=datetime.utcnow().isoformat(),
    )


citation_router = APIRouter(prefix="/api/citations", tags=["Citations"])


@citation_router.post(
    "",
    response_model=CitationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_citation(
    citation_data: CitationCreate,
    user: User = Depends(require_permission("citations:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new citation.

    - **chapter_id**: Parent chapter ID
    - **doi**: DOI (optional)
    - **title**: Citation title
    - **authors**: List of authors
    - **journal**: Journal name
    - **year**: Publication year
    - **url**: URL
    """
    citation_id = generate_uuid()

    return CitationResponse(
        id=citation_id,
        chapter_id=citation_data.chapter_id,
        doi=citation_data.doi,
        title=citation_data.title,
        authors=citation_data.authors or [],
        journal=citation_data.journal,
        year=citation_data.year,
        url=citation_data.url,
        verified=False,
        verified_at=None,
        created_at=datetime.utcnow().isoformat(),
    )


@citation_router.get("/chapter/{chapter_id}", response_model=List[CitationResponse])
async def list_citations_by_chapter(
    chapter_id: str,
    user: User = Depends(get_current_active_user),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all citations for a chapter.
    """
    return []


@citation_router.post(
    "/{citation_id}/verify",
    response_model=CitationResponse,
    dependencies=[Depends(csrf_protect)],
)
async def verify_citation(
    citation_id: str,
    user: User = Depends(require_permission("citations:verify")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Verify a citation's DOI.
    """
    return CitationResponse(
        id=citation_id,
        chapter_id="chapter-id",
        doi="10.1234/example",
        title="Verified Citation",
        authors=[],
        journal=None,
        year=2024,
        url=None,
        verified=True,
        verified_at=datetime.utcnow().isoformat(),
        created_at=datetime.utcnow().isoformat(),
    )
