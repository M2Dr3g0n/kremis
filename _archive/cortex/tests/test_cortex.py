"""
Tests for Cortex class.

Tests the CORTEX layer including query routing, handle methods, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch

from kremis_cortex.cortex import Cortex
from kremis_cortex.client import KremisClient, GroundedResult, Artifact, DEFAULT_BASE_URL
from kremis_cortex.honesty_protocol import HonestResponse


class TestCortexInit:
    """Tests for Cortex initialization."""

    def test_default_initialization(self):
        """Test Cortex initializes with default server URL."""
        cortex = Cortex()
        assert cortex.server_url == DEFAULT_BASE_URL
        assert isinstance(cortex.client, KremisClient)
        assert cortex.running is False

    def test_custom_url_initialization(self):
        """Test Cortex initializes with custom server URL."""
        cortex = Cortex(server_url="http://custom:9000")
        assert cortex.server_url == "http://custom:9000"

    def test_start_success(self):
        """Test successful Cortex start."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.client.start.return_value = True
        cortex.client.get_status.return_value = {"node_count": 5, "edge_count": 10}
        cortex.client.get_stage.return_value = {"stage": "S1", "name": "Test"}

        result = cortex.start()
        assert result is True
        assert cortex.running is True

    def test_start_failure(self):
        """Test failed Cortex start."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.client.start.return_value = False

        result = cortex.start()
        assert result is False
        assert cortex.running is False

    def test_stop(self):
        """Test Cortex stop."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.running = True
        cortex.stop()
        assert cortex.running is False
        cortex.client.stop.assert_called_once()


class TestCortexQuery:
    """Tests for Cortex.query() method."""

    def _make_cortex(self):
        """Create a Cortex with a mocked client."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.running = True
        return cortex

    def test_empty_query(self):
        """Test query with empty string."""
        cortex = self._make_cortex()
        response = cortex.query("")
        assert len(response.unknowns) == 1
        assert "No query provided" in response.unknowns[0].explanation

    def test_whitespace_query(self):
        """Test query with whitespace only."""
        cortex = self._make_cortex()
        response = cortex.query("   ")
        assert len(response.unknowns) == 1

    def test_unknown_command(self):
        """Test query with unknown command."""
        cortex = self._make_cortex()
        response = cortex.query("foobar 123")
        assert len(response.unknowns) == 1
        assert "Unknown command" in response.unknowns[0].explanation

    def test_lookup_query(self):
        """Test lookup command routing."""
        cortex = self._make_cortex()
        grounded = GroundedResult(
            artifact=Artifact(path=[1, 2]),
            confidence=100,
            verified=True,
            evidence_path=[1, 2],
        )
        cortex.client.lookup.return_value = grounded

        response = cortex.query("lookup 1")
        assert len(response.facts) == 1
        cortex.client.lookup.assert_called_once_with(1)

    def test_lookup_invalid_id(self):
        """Test lookup with non-numeric ID."""
        cortex = self._make_cortex()
        response = cortex.query("lookup abc")
        assert len(response.unknowns) == 1
        assert "Invalid entity ID" in response.unknowns[0].explanation

    def test_traverse_query(self):
        """Test traverse command routing."""
        cortex = self._make_cortex()
        grounded = GroundedResult(
            artifact=Artifact(path=[1, 2, 3]),
            confidence=100,
            verified=True,
            evidence_path=[1, 2, 3],
        )
        cortex.client.traverse.return_value = grounded

        response = cortex.query("traverse 1 3")
        assert len(response.facts) == 1
        cortex.client.traverse.assert_called_once_with(1, 3)

    def test_traverse_default_depth(self):
        """Test traverse with default depth."""
        cortex = self._make_cortex()
        grounded = GroundedResult(
            artifact=Artifact(path=[1]),
            confidence=100,
            verified=True,
            evidence_path=[1],
        )
        cortex.client.traverse.return_value = grounded

        response = cortex.query("traverse 1")
        cortex.client.traverse.assert_called_once_with(1, 3)

    def test_traverse_invalid_depth(self):
        """Test traverse with invalid depth value."""
        cortex = self._make_cortex()
        response = cortex.query("traverse 1 abc")
        assert len(response.unknowns) == 1
        assert "Invalid depth value" in response.unknowns[0].explanation

    def test_path_query(self):
        """Test path command routing."""
        cortex = self._make_cortex()
        grounded = GroundedResult(
            artifact=Artifact(path=[1, 5, 10]),
            confidence=100,
            verified=True,
            evidence_path=[1, 5, 10],
        )
        cortex.client.strongest_path.return_value = grounded

        response = cortex.query("path 1 10")
        assert len(response.facts) == 1
        cortex.client.strongest_path.assert_called_once_with(1, 10)

    def test_path_invalid_ids(self):
        """Test path with non-numeric IDs."""
        cortex = self._make_cortex()
        response = cortex.query("path abc def")
        assert len(response.unknowns) == 1
        assert "Invalid node IDs" in response.unknowns[0].explanation

    def test_intersect_query_missing_args(self):
        """Test intersect requires minimum arguments (routed as unknown)."""
        cortex = self._make_cortex()
        # 'intersect' is not a recognized top-level command in cortex.query
        response = cortex.query("intersect 1 2 3")
        assert len(response.unknowns) == 1

    def test_status_query(self):
        """Test status command routing."""
        cortex = self._make_cortex()
        cortex.client.get_status.return_value = {
            "node_count": 10,
            "edge_count": 15,
            "stable_edges": 5,
        }

        response = cortex.query("status")
        assert len(response.facts) == 1
        assert "10 nodes" in response.facts[0].statement

    def test_status_failure(self):
        """Test status when server returns None."""
        cortex = self._make_cortex()
        cortex.client.get_status.return_value = None

        response = cortex.query("status")
        assert len(response.unknowns) == 1
        assert "Could not retrieve status" in response.unknowns[0].explanation

    def test_stage_query(self):
        """Test stage command routing."""
        cortex = self._make_cortex()
        cortex.client.get_stage.return_value = {
            "stage": "S1",
            "name": "Pattern Crystallization",
            "progress_percent": 45,
        }

        response = cortex.query("stage")
        assert len(response.facts) == 1
        assert "S1" in response.facts[0].statement

    def test_stage_failure(self):
        """Test stage when server returns None."""
        cortex = self._make_cortex()
        cortex.client.get_stage.return_value = None

        response = cortex.query("stage")
        assert len(response.unknowns) == 1
        assert "Could not retrieve stage" in response.unknowns[0].explanation

    def test_ingest_query(self):
        """Test ingest command routing."""
        cortex = self._make_cortex()
        cortex.client.ingest_signal.return_value = 42

        response = cortex.query("ingest 1 name Alice")
        assert len(response.facts) == 1
        assert "Signal ingested" in response.facts[0].statement
        cortex.client.ingest_signal.assert_called_once_with(1, "name", "Alice")

    def test_ingest_failure(self):
        """Test ingest when server returns None."""
        cortex = self._make_cortex()
        cortex.client.ingest_signal.return_value = None

        response = cortex.query("ingest 1 name Alice")
        assert len(response.unknowns) == 1
        assert "Failed to ingest" in response.unknowns[0].explanation

    def test_ingest_invalid_entity_id(self):
        """Test ingest with non-numeric entity ID."""
        cortex = self._make_cortex()
        response = cortex.query("ingest abc name Alice")
        assert len(response.unknowns) == 1
        assert "Invalid entity ID" in response.unknowns[0].explanation

    def test_ingest_multiword_value(self):
        """Test ingest with multi-word value."""
        cortex = self._make_cortex()
        cortex.client.ingest_signal.return_value = 99

        response = cortex.query("ingest 1 description hello world foo")
        cortex.client.ingest_signal.assert_called_once_with(1, "description", "hello world foo")


class TestCortexHandleLookupNone:
    """Test _handle_lookup when Core returns None."""

    def test_lookup_core_returns_none(self):
        """Test lookup when Core returns None (unverified)."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.client.lookup.return_value = None

        response = cortex.query("lookup 42")
        # When Core returns None, verify_hypothesis marks as UNKNOWN
        assert len(response.unknowns) == 1


class TestCortexHandleTraverseNone:
    """Test _handle_traverse when Core returns None."""

    def test_traverse_core_returns_none(self):
        """Test traverse when Core returns None."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.client.traverse.return_value = None

        response = cortex.query("traverse 1")
        assert len(response.unknowns) == 1


class TestCortexHandlePathNone:
    """Test _handle_path when Core returns None."""

    def test_path_core_returns_none(self):
        """Test path when Core returns None."""
        cortex = Cortex()
        cortex.client = MagicMock()
        cortex.client.strongest_path.return_value = None

        response = cortex.query("path 1 10")
        assert len(response.unknowns) == 1
