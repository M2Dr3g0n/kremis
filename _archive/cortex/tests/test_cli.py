"""
Tests for CORTEX CLI.

Tests command-line interface argument parsing and command routing.
"""

import pytest
from unittest.mock import MagicMock, patch

from kremis_cortex.cli import main, cmd_repl, cmd_status, cmd_query
from kremis_cortex.client import DEFAULT_BASE_URL


class TestCmdRepl:
    """Tests for cmd_repl function."""

    def test_cmd_repl_start_failure(self):
        """Test cmd_repl when server connection fails."""
        with patch("kremis_cortex.cli.Cortex") as MockCortex:
            mock_cortex = MagicMock()
            mock_cortex.start.return_value = False
            MockCortex.return_value = mock_cortex

            args = MagicMock()
            args.server = DEFAULT_BASE_URL

            result = cmd_repl(args)
            assert result == 1

    def test_cmd_repl_start_success(self):
        """Test cmd_repl when server connection succeeds."""
        with patch("kremis_cortex.cli.Cortex") as MockCortex:
            mock_cortex = MagicMock()
            mock_cortex.start.return_value = True
            MockCortex.return_value = mock_cortex

            args = MagicMock()
            args.server = DEFAULT_BASE_URL

            result = cmd_repl(args)
            assert result == 0
            mock_cortex.repl.assert_called_once()
            mock_cortex.stop.assert_called_once()


class TestCmdStatus:
    """Tests for cmd_status function."""

    def test_cmd_status_success(self):
        """Test cmd_status with connected server."""
        with patch("kremis_cortex.cli.KremisClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start.return_value = True
            mock_client.get_status.return_value = {
                "node_count": 10,
                "edge_count": 15,
                "stable_edges": 5,
            }
            mock_client.get_stage.return_value = {
                "stage": "S1",
                "name": "Pattern Crystallization",
                "progress_percent": 45,
            }
            MockClient.return_value = mock_client

            args = MagicMock()
            args.server = DEFAULT_BASE_URL

            result = cmd_status(args)
            assert result == 0
            mock_client.stop.assert_called_once()

    def test_cmd_status_connection_failure(self):
        """Test cmd_status when server is unreachable."""
        with patch("kremis_cortex.cli.KremisClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start.return_value = False
            MockClient.return_value = mock_client

            args = MagicMock()
            args.server = DEFAULT_BASE_URL

            result = cmd_status(args)
            assert result == 1

    def test_cmd_status_no_stage(self):
        """Test cmd_status when stage returns None."""
        with patch("kremis_cortex.cli.KremisClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start.return_value = True
            mock_client.get_status.return_value = {"node_count": 5, "edge_count": 3, "stable_edges": 1}
            mock_client.get_stage.return_value = None
            MockClient.return_value = mock_client

            args = MagicMock()
            args.server = DEFAULT_BASE_URL

            result = cmd_status(args)
            assert result == 0


class TestCmdQuery:
    """Tests for cmd_query function."""

    def test_cmd_query_success(self):
        """Test cmd_query with successful execution."""
        with patch("kremis_cortex.cli.Cortex") as MockCortex:
            mock_cortex = MagicMock()
            mock_client = MagicMock()
            mock_client.start.return_value = True
            mock_cortex.client = mock_client

            mock_response = MagicMock()
            mock_response.to_text.return_value = "test output"
            mock_cortex.query.return_value = mock_response
            MockCortex.return_value = mock_cortex

            args = MagicMock()
            args.server = DEFAULT_BASE_URL
            args.query_string = "lookup 1"

            result = cmd_query(args)
            assert result == 0
            mock_cortex.query.assert_called_once_with("lookup 1")

    def test_cmd_query_connection_failure(self):
        """Test cmd_query when server connection fails."""
        with patch("kremis_cortex.cli.Cortex") as MockCortex:
            mock_cortex = MagicMock()
            mock_cortex.start.return_value = False
            MockCortex.return_value = mock_cortex

            args = MagicMock()
            args.server = DEFAULT_BASE_URL
            args.query_string = "status"

            result = cmd_query(args)
            assert result == 1


class TestMainArgParsing:
    """Tests for main() argument routing."""

    def test_main_no_args_defaults_to_repl(self):
        """Test main with no arguments defaults to REPL."""
        with patch("kremis_cortex.cli.cmd_repl", return_value=0) as mock_repl:
            with patch("sys.argv", ["kremis-cortex"]):
                result = main()
                assert result == 0
                mock_repl.assert_called_once()

    def test_main_repl_subcommand(self):
        """Test main with 'repl' subcommand."""
        with patch("kremis_cortex.cli.cmd_repl", return_value=0) as mock_repl:
            with patch("sys.argv", ["kremis-cortex", "repl"]):
                result = main()
                assert result == 0
                mock_repl.assert_called_once()

    def test_main_status_subcommand(self):
        """Test main with 'status' subcommand."""
        with patch("kremis_cortex.cli.cmd_status", return_value=0) as mock_status:
            with patch("sys.argv", ["kremis-cortex", "status"]):
                result = main()
                assert result == 0
                mock_status.assert_called_once()

    def test_main_query_subcommand(self):
        """Test main with 'query' subcommand."""
        with patch("kremis_cortex.cli.cmd_query", return_value=0) as mock_query:
            with patch("sys.argv", ["kremis-cortex", "query", "lookup 1"]):
                result = main()
                assert result == 0
                mock_query.assert_called_once()

    def test_main_custom_server(self):
        """Test main with custom --server flag."""
        with patch("kremis_cortex.cli.cmd_status", return_value=0) as mock_status:
            with patch("sys.argv", ["kremis-cortex", "--server", "http://custom:9000", "status"]):
                result = main()
                assert result == 0
                args = mock_status.call_args[0][0]
                assert args.server == "http://custom:9000"
