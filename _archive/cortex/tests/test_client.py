"""
Tests for Kremis Client.

Tests HTTP communication with mocked server responses.
"""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from kremis_cortex.client import (
    KremisClient,
    AsyncKremisClient,
    Artifact,
    GroundedResult,
    QueryResult,
    DEFAULT_BASE_URL,
)


class TestArtifact:
    """Tests for Artifact dataclass."""

    def test_artifact_creation(self):
        """Test basic artifact creation."""
        artifact = Artifact(path=[1, 2, 3])
        assert artifact.path == [1, 2, 3]
        assert artifact.subgraph is None

    def test_artifact_with_subgraph(self):
        """Test artifact with subgraph."""
        artifact = Artifact(
            path=[1, 2, 3],
            subgraph=[(1, 2, 10), (2, 3, 15)],
        )
        assert artifact.path == [1, 2, 3]
        assert len(artifact.subgraph) == 2
        assert artifact.subgraph[0] == (1, 2, 10)


class TestGroundedResult:
    """Tests for GroundedResult dataclass."""

    def test_grounded_result_verified(self, sample_artifact):
        """Test verified grounded result."""
        result = GroundedResult(
            artifact=sample_artifact,
            confidence=100,
            verified=True,
            evidence_path=[1, 2, 3],
        )
        assert result.verified is True
        assert result.confidence == 100
        assert result.evidence_path == [1, 2, 3]

    def test_grounded_result_unverified(self):
        """Test unverified grounded result."""
        result = GroundedResult(
            artifact=None,
            confidence=0,
            verified=False,
            evidence_path=[],
        )
        assert result.verified is False
        assert result.artifact is None


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_query_result_success(self):
        """Test successful query result."""
        result = QueryResult(success=True, data={"path": [1, 2]})
        assert result.success is True
        assert result.data == {"path": [1, 2]}
        assert result.error is None

    def test_query_result_failure(self):
        """Test failed query result."""
        result = QueryResult(success=False, data=None, error="Connection failed")
        assert result.success is False
        assert result.error == "Connection failed"


class TestKremisClient:
    """Tests for KremisClient."""

    def test_client_initialization(self):
        """Test client initialization with default URL."""
        client = KremisClient()
        assert client.base_url == DEFAULT_BASE_URL.rstrip("/")
        assert client.timeout == 30.0

    def test_client_custom_url(self):
        """Test client with custom URL."""
        client = KremisClient(base_url="http://custom:9000/")
        assert client.base_url == "http://custom:9000"

    def test_start_success(self, httpx_mock: HTTPXMock, mock_health_response):
        """Test successful client start."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        client = KremisClient()
        assert client.start() is True
        client.stop()

    def test_start_failure(self, httpx_mock: HTTPXMock):
        """Test failed client start (server unreachable)."""
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        client = KremisClient()
        assert client.start() is False

    def test_stop(self, httpx_mock: HTTPXMock, mock_health_response):
        """Test client stop."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        client = KremisClient()
        client.start()
        client.stop()
        assert client._client is None

    def test_get_status(self, httpx_mock: HTTPXMock, mock_health_response, mock_status_response):
        """Test get_status method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/status",
            json=mock_status_response,
        )
        client = KremisClient()
        client.start()
        status = client.get_status()
        assert status is not None
        assert status["node_count"] == 10
        assert status["edge_count"] == 15
        client.stop()

    def test_get_stage(self, httpx_mock: HTTPXMock, mock_health_response, mock_stage_response):
        """Test get_stage method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/stage",
            json=mock_stage_response,
        )
        client = KremisClient()
        client.start()
        stage = client.get_stage()
        assert stage is not None
        assert stage["stage"] == "S1"
        assert stage["progress_percent"] == 45
        client.stop()

    def test_ingest_signal(self, httpx_mock: HTTPXMock, mock_health_response, mock_ingest_response):
        """Test ingest_signal method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/signal",
            json=mock_ingest_response,
        )
        client = KremisClient()
        client.start()
        node_id = client.ingest_signal(1, "name", "Alice")
        assert node_id == 42
        client.stop()

    def test_lookup_found(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test lookup with found entity."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = KremisClient()
        client.start()
        result = client.lookup(1)
        assert result is not None
        assert result.verified is True
        assert result.evidence_path == [1, 2, 3]
        client.stop()

    def test_lookup_not_found(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_not_found):
        """Test lookup with not found entity."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_not_found,
        )
        client = KremisClient()
        client.start()
        result = client.lookup(999)
        assert result is not None
        assert result.verified is False
        client.stop()

    def test_traverse(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test traverse method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = KremisClient()
        client.start()
        result = client.traverse(1, depth=3)
        assert result is not None
        assert result.evidence_path == [1, 2, 3]
        client.stop()

    def test_strongest_path(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test strongest_path method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = KremisClient()
        client.start()
        result = client.strongest_path(1, 3)
        assert result is not None
        assert result.evidence_path == [1, 2, 3]
        client.stop()

    def test_client_not_started(self):
        """Test operations on non-started client."""
        client = KremisClient()
        # Should return None when client not started
        assert client.get_status() is None
        assert client.lookup(1) is None


class TestAsyncKremisClient:
    """Tests for AsyncKremisClient."""

    @pytest.mark.asyncio
    async def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncKremisClient()
        assert client.base_url == DEFAULT_BASE_URL.rstrip("/")

    @pytest.mark.asyncio
    async def test_async_start_success(self, httpx_mock: HTTPXMock, mock_health_response):
        """Test async client start."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        client = AsyncKremisClient()
        assert await client.start() is True
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_lookup(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test async lookup method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = AsyncKremisClient()
        await client.start()
        result = await client.lookup(1)
        assert result is not None
        assert result.verified is True
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_traverse(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test async traverse method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = AsyncKremisClient()
        await client.start()
        result = await client.traverse(1, depth=3)
        assert result is not None
        assert result.evidence_path == [1, 2, 3]
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_strongest_path(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test async strongest_path method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = AsyncKremisClient()
        await client.start()
        result = await client.strongest_path(1, 3)
        assert result is not None
        assert result.evidence_path == [1, 2, 3]
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_intersect(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test async intersect method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = AsyncKremisClient()
        await client.start()
        result = await client.intersect([1, 2, 3])
        assert result is not None
        assert result.verified is True
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_related(self, httpx_mock: HTTPXMock, mock_health_response, mock_query_response_found):
        """Test async related method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/query",
            json=mock_query_response_found,
        )
        client = AsyncKremisClient()
        await client.start()
        result = await client.related(1, depth=2)
        assert result is not None
        assert result.evidence_path == [1, 2, 3]
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_ingest_signal(self, httpx_mock: HTTPXMock, mock_health_response, mock_ingest_response):
        """Test async ingest_signal method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/signal",
            json=mock_ingest_response,
        )
        client = AsyncKremisClient()
        await client.start()
        node_id = await client.ingest_signal(1, "name", "Alice")
        assert node_id == 42
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_get_status(self, httpx_mock: HTTPXMock, mock_health_response, mock_status_response):
        """Test async get_status method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/status",
            json=mock_status_response,
        )
        client = AsyncKremisClient()
        await client.start()
        status = await client.get_status()
        assert status is not None
        assert status["node_count"] == 10
        assert status["edge_count"] == 15
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_get_stage(self, httpx_mock: HTTPXMock, mock_health_response, mock_stage_response):
        """Test async get_stage method."""
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json=mock_health_response,
        )
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/stage",
            json=mock_stage_response,
        )
        client = AsyncKremisClient()
        await client.start()
        stage = await client.get_stage()
        assert stage is not None
        assert stage["stage"] == "S1"
        assert stage["progress_percent"] == 45
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_timeout(self, httpx_mock: HTTPXMock):
        """Test async client timeout handling."""
        import httpx as httpx_mod
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json={"status": "ok"},
        )
        httpx_mock.add_exception(
            httpx_mod.ReadTimeout("Connection timed out"),
            url=f"{DEFAULT_BASE_URL}/query",
        )
        client = AsyncKremisClient(timeout=0.1)
        await client.start()
        result = await client.lookup(1)
        assert result is None
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_timeout_get(self, httpx_mock: HTTPXMock):
        """Test async client timeout on GET request."""
        import httpx as httpx_mod
        httpx_mock.add_response(
            url=f"{DEFAULT_BASE_URL}/health",
            json={"status": "ok"},
        )
        httpx_mock.add_exception(
            httpx_mod.ReadTimeout("Connection timed out"),
            url=f"{DEFAULT_BASE_URL}/status",
        )
        client = AsyncKremisClient(timeout=0.1)
        await client.start()
        status = await client.get_status()
        assert status is None
        await client.stop()

    @pytest.mark.asyncio
    async def test_async_client_not_started(self):
        """Test async operations on non-started client."""
        client = AsyncKremisClient()
        assert await client.get_status() is None
        assert await client.lookup(1) is None
