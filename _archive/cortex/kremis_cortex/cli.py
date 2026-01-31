#!/usr/bin/env python3
"""
CORTEX CLI - Command-line interface for Kremis CORTEX.

Usage:
    kremis-cortex repl          # Interactive REPL
    kremis-cortex query COMMAND # Single query
    kremis-cortex status        # Show connection status
"""

import argparse
import sys
from .cortex import Cortex
from .client import KremisClient, DEFAULT_BASE_URL


def cmd_repl(args: argparse.Namespace) -> int:
    """Start interactive REPL.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    cortex = Cortex(server_url=args.server)
    if cortex.start():
        try:
            cortex.repl()
        finally:
            cortex.stop()
        return 0
    else:
        print(f"Error: Could not connect to Kremis server at {args.server}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show connection status.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    client = KremisClient(base_url=args.server)
    if client.start():
        status = client.get_status()
        stage = client.get_stage()

        print(f"Connected to: {args.server}")
        print()

        if status:
            print("Graph Status:")
            print(f"  Nodes: {status.get('node_count', 0)}")
            print(f"  Edges: {status.get('edge_count', 0)}")
            print(f"  Stable Edges: {status.get('stable_edges', 0)}")
            print()

        if stage:
            print("Developmental Stage:")
            print(f"  Stage: {stage.get('stage', 'Unknown')}")
            print(f"  Name: {stage.get('name', 'Unknown')}")
            print(f"  Progress: {stage.get('progress_percent', 0)}%")
            print()

        client.stop()
        return 0
    else:
        print(f"Error: Could not connect to {args.server}")
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    """Execute a single query.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    cortex = Cortex(server_url=args.server)
    if not cortex.start():
        print("Error: Cannot connect to Kremis server")
        return 1
    try:
        result = cortex.query(args.query_string)
        print(result.to_text())
        return 0
    finally:
        cortex.stop()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="kremis-cortex",
        description="Cortex - Honest AGI layer for Kremis"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_BASE_URL,
        help=f"Kremis server URL (default: {DEFAULT_BASE_URL})"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # REPL command
    repl_parser = subparsers.add_parser("repl", help="Start interactive REPL")
    repl_parser.set_defaults(func=cmd_repl)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show connection status")
    status_parser.set_defaults(func=cmd_status)

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a single query")
    query_parser.add_argument("query_string", help="Query to execute (e.g., 'lookup 1')")
    query_parser.set_defaults(func=cmd_query)

    args = parser.parse_args()

    if args.command is None:
        # Default to REPL if no command specified
        args.func = cmd_repl

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
