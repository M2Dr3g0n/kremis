"""
Pytest fixtures for Kremis CORTEX tests.
"""

import pytest
from kremis_cortex.client import Artifact, GroundedResult
from kremis_cortex.honesty_protocol import get_audit_log


@pytest.fixture
def mock_health_response():
    """Mock health endpoint response."""
    return {"status": "ok", "version": "0.1.0"}


@pytest.fixture
def mock_status_response():
    """Mock status endpoint response."""
    return {
        "node_count": 10,
        "edge_count": 15,
        "stable_edges": 5,
        "density_millionths": 150000,
    }


@pytest.fixture
def mock_stage_response():
    """Mock stage endpoint response."""
    return {
        "stage": "S1",
        "name": "Pattern Crystallization",
        "progress_percent": 45,
        "stable_edges_needed": 100,
        "stable_edges_current": 45,
    }


@pytest.fixture
def mock_ingest_response():
    """Mock signal ingest response."""
    return {"success": True, "node_id": 42, "error": None}


@pytest.fixture
def mock_query_response_found():
    """Mock query response with found result."""
    return {
        "success": True,
        "found": True,
        "path": [1, 2, 3],
        "edges": [
            {"from": 1, "to": 2, "weight": 10},
            {"from": 2, "to": 3, "weight": 15},
        ],
        "error": None,
    }


@pytest.fixture
def mock_query_response_not_found():
    """Mock query response with not found result."""
    return {
        "success": True,
        "found": False,
        "path": [],
        "edges": [],
        "error": None,
    }


@pytest.fixture
def sample_artifact():
    """Sample artifact for testing."""
    return Artifact(path=[1, 2, 3], subgraph=[(1, 2, 10), (2, 3, 15)])


@pytest.fixture
def sample_grounded_result_verified(sample_artifact):
    """Sample verified grounded result."""
    return GroundedResult(
        artifact=sample_artifact,
        confidence=100,
        verified=True,
        evidence_path=[1, 2, 3],
    )


@pytest.fixture
def sample_grounded_result_partial(sample_artifact):
    """Sample partial grounded result."""
    return GroundedResult(
        artifact=sample_artifact,
        confidence=65,
        verified=False,
        evidence_path=[1, 2],
    )


@pytest.fixture(autouse=True)
def clear_audit_log():
    """Clear audit log before each test."""
    get_audit_log().clear()
    yield
    get_audit_log().clear()
