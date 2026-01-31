"""
Kremis Client - Communication with Kremis Core via HTTP REST API.

Per ROADMAP.md Section 10.5:
- Uses ONLY public Facet APIs (HTTP endpoints)
- No direct access to kremis-core internals
"""

import json
import warnings

import httpx
from dataclasses import dataclass
from typing import Any

# Default server URL
DEFAULT_BASE_URL = "http://localhost:8080"


@dataclass
class Artifact:
    """Represents a graph artifact returned by Core."""
    path: list[int]
    subgraph: list[tuple[int, int, int]] | None = None


@dataclass
class GroundedResult:
    """Result from a grounding query."""
    artifact: Artifact | None
    confidence: int  # 0-100
    verified: bool
    evidence_path: list[int]


@dataclass
class QueryResult:
    """Result from any Core query."""
    success: bool
    data: Any | None
    error: str | None = None


def _validate_signal_input(entity_id: int, attribute: str, value: str) -> None:
    """Validate signal input parameters."""
    if not isinstance(entity_id, int) or entity_id < 0:
        raise ValueError(f"entity_id must be a non-negative integer, got {entity_id!r}")
    if not isinstance(attribute, str) or not attribute:
        raise ValueError("attribute must be a non-empty string")
    if len(attribute.encode("utf-8")) > 256:
        raise ValueError(f"attribute exceeds 256 bytes limit ({len(attribute.encode('utf-8'))} bytes)")
    if not isinstance(value, str) or not value:
        raise ValueError("value must be a non-empty string")
    if len(value.encode("utf-8")) > 65536:
        raise ValueError(f"value exceeds 64KB limit ({len(value.encode('utf-8'))} bytes)")


def _validate_depth(depth: int) -> None:
    """Validate traversal depth parameter."""
    if not isinstance(depth, int) or depth < 0 or depth > 100:
        raise ValueError(f"depth must be an integer between 0 and 100, got {depth!r}")


def _validate_node_id(node_id: int) -> None:
    """Validate node ID parameter."""
    if not isinstance(node_id, int) or node_id < 0:
        raise ValueError(f"node_id must be a non-negative integer, got {node_id!r}")


def _parse_query_response(data: dict) -> GroundedResult:
    """Parse a QueryResponse into GroundedResult."""
    found = data.get("found", False)
    path = data.get("path", [])
    edges = data.get("edges", [])

    artifact = None
    if found and path:
        subgraph = None
        if edges:
            subgraph = [(e["from"], e["to"], e["weight"]) for e in edges]
        artifact = Artifact(path=path, subgraph=subgraph)

    return GroundedResult(
        artifact=artifact,
        confidence=100 if found else 0,
        verified=found,
        evidence_path=path,
    )


class KremisClient:
    """
    Client for communicating with Kremis Core via HTTP.

    Uses REST API for communication (replaces stdio JSON protocol).
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the Kremis HTTP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.Client | None = None

        if not self.base_url.startswith("https://") and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            warnings.warn(
                f"Using unencrypted HTTP connection to {self.base_url}. "
                "Consider using HTTPS for non-localhost connections.",
                UserWarning,
                stacklevel=2,
            )

    def start(self) -> bool:
        """Initialize the HTTP client and verify connectivity."""
        try:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            # Health check
            response = self._client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            if self._client is not None:
                self._client.close()
                self._client = None
            return False

    def stop(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def _post(self, endpoint: str, json_data: dict) -> QueryResult:
        """Send a POST request and return QueryResult."""
        if not self._client:
            return QueryResult(success=False, data=None, error="Client not started")

        try:
            response = self._client.post(endpoint, json=json_data)
            response.raise_for_status()
            data = response.json()
            return QueryResult(
                success=data.get("success", False),
                data=data,
                error=data.get("error"),
            )
        except httpx.HTTPStatusError as e:
            return QueryResult(success=False, data=None, error=f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            return QueryResult(success=False, data=None, error=str(e))
        except json.JSONDecodeError as e:
            return QueryResult(success=False, data=None, error=f"Invalid JSON response: {e}")
        except Exception as e:
            return QueryResult(success=False, data=None, error=str(e))

    def _get(self, endpoint: str) -> QueryResult:
        """Send a GET request and return QueryResult."""
        if not self._client:
            return QueryResult(success=False, data=None, error="Client not started")

        try:
            response = self._client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            return QueryResult(success=True, data=data, error=None)
        except httpx.HTTPStatusError as e:
            return QueryResult(success=False, data=None, error=f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            return QueryResult(success=False, data=None, error=str(e))
        except json.JSONDecodeError as e:
            return QueryResult(success=False, data=None, error=f"Invalid JSON response: {e}")
        except Exception as e:
            return QueryResult(success=False, data=None, error=str(e))

    def lookup(self, entity_id: int) -> GroundedResult | None:
        """
        Look up an entity in the graph.

        Args:
            entity_id: The entity ID to look up

        Returns:
            GroundedResult if found, None otherwise
        """
        result = self._post("/query", {
            "type": "lookup",
            "entity_id": entity_id,
        })

        if not result.success or result.data is None:
            return None

        return _parse_query_response(result.data)

    def traverse(self, start_node: int, depth: int = 3) -> GroundedResult | None:
        """
        Traverse the graph from a starting node.

        Args:
            start_node: NodeId to start from
            depth: Maximum traversal depth

        Returns:
            GroundedResult with traversal artifact
        """
        _validate_node_id(start_node)
        _validate_depth(depth)
        result = self._post("/query", {
            "type": "traverse",
            "node_id": start_node,
            "depth": depth,
        })

        if not result.success or result.data is None:
            return None

        return _parse_query_response(result.data)

    def strongest_path(self, start: int, end: int) -> GroundedResult | None:
        """
        Find the strongest path between two nodes.

        Args:
            start: Starting NodeId
            end: Ending NodeId

        Returns:
            GroundedResult with path, None if no path exists
        """
        _validate_node_id(start)
        _validate_node_id(end)
        result = self._post("/query", {
            "type": "strongest_path",
            "start": start,
            "end": end,
        })

        if not result.success or result.data is None:
            return None

        return _parse_query_response(result.data)

    def intersect(self, nodes: list[int]) -> GroundedResult | None:
        """
        Find nodes connected to ALL input nodes.

        Args:
            nodes: List of NodeIds to intersect

        Returns:
            GroundedResult with common connections
        """
        result = self._post("/query", {
            "type": "intersect",
            "nodes": nodes,
        })

        if not result.success or result.data is None:
            return None

        return _parse_query_response(result.data)

    def related(self, node_id: int, depth: int = 3) -> GroundedResult | None:
        """
        Extract related subgraph from a node.

        Args:
            node_id: Starting NodeId
            depth: Maximum depth

        Returns:
            GroundedResult with subgraph
        """
        _validate_node_id(node_id)
        _validate_depth(depth)
        result = self._post("/query", {
            "type": "related",
            "node_id": node_id,
            "depth": depth,
        })

        if not result.success or result.data is None:
            return None

        return _parse_query_response(result.data)

    def ingest_signal(self, entity_id: int, attribute: str, value: str) -> int | None:
        """
        Ingest a signal into the graph.

        Args:
            entity_id: Entity ID
            attribute: Attribute name
            value: Attribute value

        Returns:
            NodeId of created/existing node, None on error
        """
        _validate_signal_input(entity_id, attribute, value)
        result = self._post("/signal", {
            "entity_id": entity_id,
            "attribute": attribute,
            "value": value,
        })

        if not result.success or result.data is None:
            return None

        return result.data.get("node_id")

    def get_status(self) -> dict | None:
        """
        Get graph status.

        Returns:
            Dict with node_count, edge_count, stable_edges, density_millionths
        """
        result = self._get("/status")
        return result.data if result.success else None

    def get_stage(self) -> dict | None:
        """
        Get developmental stage.

        Returns:
            Dict with stage, name, progress_percent, etc.
        """
        result = self._get("/stage")
        return result.data if result.success else None


class AsyncKremisClient:
    """
    Async version of KremisClient using httpx.AsyncClient.

    Use this for concurrent operations.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

        if not self.base_url.startswith("https://") and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            warnings.warn(
                f"Using unencrypted HTTP connection to {self.base_url}. "
                "Consider using HTTPS for non-localhost connections.",
                UserWarning,
                stacklevel=2,
            )

    async def start(self) -> bool:
        """Initialize the async HTTP client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            response = await self._client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            if self._client is not None:
                await self._client.aclose()
                self._client = None
            return False

    async def stop(self) -> None:
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        return False

    async def _post(self, endpoint: str, json_data: dict) -> QueryResult:
        """Send a POST request asynchronously."""
        if not self._client:
            return QueryResult(success=False, data=None, error="Client not started")

        try:
            response = await self._client.post(endpoint, json=json_data)
            response.raise_for_status()
            data = response.json()
            return QueryResult(
                success=data.get("success", False),
                data=data,
                error=data.get("error"),
            )
        except httpx.HTTPStatusError as e:
            return QueryResult(success=False, data=None, error=f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            return QueryResult(success=False, data=None, error=str(e))
        except json.JSONDecodeError as e:
            return QueryResult(success=False, data=None, error=f"Invalid JSON response: {e}")
        except Exception as e:
            return QueryResult(success=False, data=None, error=str(e))

    async def _get(self, endpoint: str) -> QueryResult:
        """Send a GET request asynchronously."""
        if not self._client:
            return QueryResult(success=False, data=None, error="Client not started")

        try:
            response = await self._client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            return QueryResult(success=True, data=data, error=None)
        except httpx.HTTPStatusError as e:
            return QueryResult(success=False, data=None, error=f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            return QueryResult(success=False, data=None, error=str(e))
        except json.JSONDecodeError as e:
            return QueryResult(success=False, data=None, error=f"Invalid JSON response: {e}")
        except Exception as e:
            return QueryResult(success=False, data=None, error=str(e))

    async def lookup(self, entity_id: int) -> GroundedResult | None:
        """Look up an entity (async)."""
        result = await self._post("/query", {
            "type": "lookup",
            "entity_id": entity_id,
        })
        if not result.success or result.data is None:
            return None
        return _parse_query_response(result.data)

    async def traverse(self, start_node: int, depth: int = 3) -> GroundedResult | None:
        """Traverse the graph (async)."""
        _validate_node_id(start_node)
        _validate_depth(depth)
        result = await self._post("/query", {
            "type": "traverse",
            "node_id": start_node,
            "depth": depth,
        })
        if not result.success or result.data is None:
            return None
        return _parse_query_response(result.data)

    async def strongest_path(self, start: int, end: int) -> GroundedResult | None:
        """Find strongest path (async)."""
        _validate_node_id(start)
        _validate_node_id(end)
        result = await self._post("/query", {
            "type": "strongest_path",
            "start": start,
            "end": end,
        })
        if not result.success or result.data is None:
            return None
        return _parse_query_response(result.data)

    async def intersect(self, nodes: list[int]) -> GroundedResult | None:
        """
        Find nodes connected to ALL input nodes (async).

        Args:
            nodes: List of NodeIds to intersect

        Returns:
            GroundedResult with common connections
        """
        result = await self._post("/query", {
            "type": "intersect",
            "nodes": nodes,
        })
        if not result.success or result.data is None:
            return None
        return _parse_query_response(result.data)

    async def related(self, node_id: int, depth: int = 3) -> GroundedResult | None:
        """
        Extract related subgraph from a node (async).

        Args:
            node_id: Starting NodeId
            depth: Maximum depth

        Returns:
            GroundedResult with subgraph
        """
        _validate_node_id(node_id)
        _validate_depth(depth)
        result = await self._post("/query", {
            "type": "related",
            "node_id": node_id,
            "depth": depth,
        })
        if not result.success or result.data is None:
            return None
        return _parse_query_response(result.data)

    async def ingest_signal(self, entity_id: int, attribute: str, value: str) -> int | None:
        """Ingest a signal (async)."""
        _validate_signal_input(entity_id, attribute, value)
        result = await self._post("/signal", {
            "entity_id": entity_id,
            "attribute": attribute,
            "value": value,
        })
        if not result.success or result.data is None:
            return None
        return result.data.get("node_id")

    async def get_status(self) -> dict | None:
        """Get graph status (async)."""
        result = await self._get("/status")
        return result.data if result.success else None

    async def get_stage(self) -> dict | None:
        """Get developmental stage (async)."""
        result = await self._get("/stage")
        return result.data if result.success else None
