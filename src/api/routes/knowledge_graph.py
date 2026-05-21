"""
Knowledge Graph Routes

Handles knowledge graph operations:
- GET /api/knowledge-graph/nodes - List nodes
- POST /api/knowledge-graph/nodes - Create node
- GET /api/knowledge-graph/nodes/{id} - Get node details
- GET /api/knowledge-graph/edges - List edges
- POST /api/knowledge-graph/edges - Create edge
- GET /api/knowledge-graph/query - Query graph
"""

from datetime import datetime
from typing import Optional, List, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from pydantic import BaseModel

from api.schemas.common import SuccessResponse
from api.deps import (
    get_db,
    get_current_active_user,
    DatabaseSession,
    User,
    require_permission,
    require_role,
    generate_uuid,
)
from api.middleware.csrf import csrf_protect

router = APIRouter(prefix="/api/knowledge-graph", tags=["Knowledge Graph"])


class NodeCreate(BaseModel):
    node_type: str
    properties: dict


class NodeResponse(BaseModel):
    id: str
    node_type: str
    properties: dict
    created_at: str
    updated_at: Optional[str] = None


class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    properties: Optional[dict] = None


class EdgeResponse(BaseModel):
    id: int
    source_id: str
    target_id: str
    edge_type: str
    properties: dict
    created_at: str


class GraphQueryRequest(BaseModel):
    query: str = Field(..., max_length=500)
    node_types: Optional[List[str]] = None
    max_depth: Optional[int] = Field(default=3, ge=1, le=10)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)


class GraphQueryResponse(BaseModel):
    success: bool = True
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    total_nodes: int
    total_edges: int


_in_memory_nodes: dict = {}
_in_memory_edges: dict = {}
_edge_id_counter = 0


@router.get("/nodes", response_model=List[NodeResponse])
async def list_nodes(
    node_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission("knowledge_graph:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all nodes in the knowledge graph.

    - **node_type**: Filter by node type (chapter, section, concept, term)
    - **page**: Page number
    - **per_page**: Items per page
    """
    nodes = list(_in_memory_nodes.values())

    if node_type:
        nodes = [n for n in nodes if n.get("node_type") == node_type]

    total = len(nodes)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return [NodeResponse(**n) for n in nodes[start_idx:end_idx]]


@router.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_node(
    node_data: NodeCreate,
    user: User = Depends(require_permission("knowledge_graph:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new node in the knowledge graph.

    - **node_type**: Type of node (chapter, section, concept, term)
    - **properties**: Node properties
    """
    node_id = generate_uuid()
    now = datetime.utcnow().isoformat()

    node = {
        "id": node_id,
        "node_type": node_data.node_type,
        "properties": node_data.properties,
        "created_at": now,
        "updated_at": now,
    }

    _in_memory_nodes[node_id] = node

    return NodeResponse(**node)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    user: User = Depends(require_permission("knowledge_graph:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get node details by ID.
    """
    node = _in_memory_nodes.get(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NODE_NOT_FOUND",
                    "message": "Node not found",
                }
            },
        )

    return NodeResponse(**node)


@router.put(
    "/nodes/{node_id}",
    response_model=NodeResponse,
    dependencies=[Depends(csrf_protect)],
)
async def update_node(
    node_id: str,
    properties: dict,
    user: User = Depends(require_permission("knowledge_graph:update")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Update node properties.
    """
    node = _in_memory_nodes.get(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NODE_NOT_FOUND",
                    "message": "Node not found",
                }
            },
        )

    node["properties"].update(properties)
    node["updated_at"] = datetime.utcnow().isoformat()

    return NodeResponse(**node)


@router.delete(
    "/nodes/{node_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_node(
    node_id: str,
    user: User = Depends(require_permission("knowledge_graph:delete")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete a node and its connected edges.
    """
    if node_id not in _in_memory_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NODE_NOT_FOUND",
                    "message": "Node not found",
                }
            },
        )

    del _in_memory_nodes[node_id]

    edges_to_remove = [
        eid for eid, edge in _in_memory_edges.items()
        if edge["source_id"] == node_id or edge["target_id"] == node_id
    ]
    for eid in edges_to_remove:
        del _in_memory_edges[eid]

    return SuccessResponse(
        success=True,
        message="Node deleted successfully",
    )


@router.get("/edges", response_model=List[EdgeResponse])
async def list_edges(
    edge_type: Optional[str] = Query(default=None),
    source_id: Optional[str] = Query(default=None),
    target_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission("knowledge_graph:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    List all edges in the knowledge graph.

    - **edge_type**: Filter by edge type
    - **source_id**: Filter by source node
    - **target_id**: Filter by target node
    - **page**: Page number
    - **per_page**: Items per page
    """
    edges = list(_in_memory_edges.values())

    if edge_type:
        edges = [e for e in edges if e.get("edge_type") == edge_type]
    if source_id:
        edges = [e for e in edges if e.get("source_id") == source_id]
    if target_id:
        edges = [e for e in edges if e.get("target_id") == target_id]

    total = len(edges)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return [EdgeResponse(**e) for e in edges[start_idx:end_idx]]


@router.post(
    "/edges",
    response_model=EdgeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect)],
)
async def create_edge(
    edge_data: EdgeCreate,
    user: User = Depends(require_permission("knowledge_graph:create")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Create a new edge in the knowledge graph.

    - **source_id**: Source node ID
    - **target_id**: Target node ID
    - **edge_type**: Type of edge (CONTAINS, FOLLOWS, DEFINES, USES, REFERENCES)
    - **properties**: Edge properties
    """
    global _edge_id_counter

    if edge_data.source_id not in _in_memory_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOURCE_NODE_NOT_FOUND",
                    "message": "Source node not found",
                }
            },
        )

    if edge_data.target_id not in _in_memory_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TARGET_NODE_NOT_FOUND",
                    "message": "Target node not found",
                }
            },
        )

    _edge_id_counter += 1
    edge_id = _edge_id_counter
    now = datetime.utcnow().isoformat()

    edge = {
        "id": edge_id,
        "source_id": edge_data.source_id,
        "target_id": edge_data.target_id,
        "edge_type": edge_data.edge_type,
        "properties": edge_data.properties or {},
        "created_at": now,
    }

    _in_memory_edges[edge_id] = edge

    return EdgeResponse(**edge)


@router.delete(
    "/edges/{edge_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def delete_edge(
    edge_id: int,
    user: User = Depends(require_permission("knowledge_graph:delete")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Delete an edge from the knowledge graph.
    """
    if edge_id not in _in_memory_edges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDGE_NOT_FOUND",
                    "message": "Edge not found",
                }
            },
        )

    del _in_memory_edges[edge_id]

    return SuccessResponse(
        success=True,
        message="Edge deleted successfully",
    )


@router.post("/query", response_model=GraphQueryResponse)
async def query_graph(
    query_request: GraphQueryRequest,
    user: User = Depends(require_permission("knowledge_graph:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Query the knowledge graph using traversal.

    - **query**: Query string (node type or relationship)
    - **node_types**: Filter by node types
    - **max_depth**: Maximum traversal depth
    - **limit**: Maximum results
    """
    matched_nodes = []
    matched_edges = []

    for node in _in_memory_nodes.values():
        if query_request.node_types and node.get("node_type") not in query_request.node_types:
            continue

        props_str = str(node.get("properties", {})).lower()
        if query_request.query.lower() in props_str or query_request.query.lower() in node.get("node_type", "").lower():
            matched_nodes.append(node)

    for edge in _in_memory_edges.values():
        if query_request.query.lower() in edge.get("edge_type", "").lower():
            matched_edges.append(edge)

    return GraphQueryResponse(
        success=True,
        nodes=[NodeResponse(**n) for n in matched_nodes[:query_request.limit]],
        edges=[EdgeResponse(**e) for e in matched_edges[:query_request.limit]],
        total_nodes=len(matched_nodes),
        total_edges=len(matched_edges),
    )


@router.get("/stats", response_model=dict)
async def get_graph_stats(
    user: User = Depends(require_permission("knowledge_graph:read")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Get knowledge graph statistics.
    """
    node_types = {}
    for node in _in_memory_nodes.values():
        node_type = node.get("node_type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1

    edge_types = {}
    for edge in _in_memory_edges.values():
        edge_type = edge.get("edge_type", "unknown")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    return {
        "total_nodes": len(_in_memory_nodes),
        "total_edges": len(_in_memory_edges),
        "node_types": node_types,
        "edge_types": edge_types,
    }


@router.post(
    "/initialize",
    response_model=SuccessResponse,
    dependencies=[Depends(csrf_protect)],
)
async def initialize_graph_sample_data(
    user: User = Depends(require_role("system_admin", "content_admin")),
    db: DatabaseSession = Depends(get_db),
):
    """
    Initialize graph with sample data for testing.
    """
    chapters = db.list_chapters_by_project("demo-project")
    for i, chapter in enumerate(chapters):
        node_id = chapter["id"]
        _in_memory_nodes[node_id] = {
            "id": node_id,
            "node_type": "chapter",
            "properties": {
                "title": chapter.get("title", f"Chapter {i+1}"),
                "order": chapter.get("order_num", i+1),
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    return SuccessResponse(
        success=True,
        message="Graph initialized with sample data",
    )
