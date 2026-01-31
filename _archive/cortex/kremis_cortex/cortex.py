#!/usr/bin/env python3
"""
CORTEX Implementation - Interactive REPL for Kremis.

A demonstration of "Honest AGI" using the Kremis Core via HTTP API.

Per ROADMAP.md Section 10.5:
- Uses ONLY public Facet APIs (HTTP endpoints)
- Enforces Honesty Protocol
- Outputs FACTS / INFERENCES / UNKNOWN
"""

from .client import KremisClient, DEFAULT_BASE_URL
from .honesty_protocol import (
    HonestResponse,
    verify_hypothesis,
    get_audit_log,
)


class Cortex:
    """
    CORTEX implementation communicating with Kremis via HTTP.

    Demonstrates proper Honesty Protocol usage.
    """

    def __init__(self, server_url: str = DEFAULT_BASE_URL):
        """
        Initialize the Cortex.

        Args:
            server_url: URL of the Kremis HTTP server
        """
        self.server_url = server_url
        self.client = KremisClient(base_url=server_url)
        self.running = False

    def start(self) -> bool:
        """Start the CORTEX and connect to Core via HTTP."""
        print("=" * 50)
        print("  CORTEX - Honest AGI Layer")
        print(f"  Connecting to: {self.server_url}")
        print("=" * 50)
        print()

        if not self.client.start():
            print(f"Error: Could not connect to Kremis server at {self.server_url}")
            print("Make sure the server is running: kremis server")
            return False

        # Show connection info
        status = self.client.get_status()
        if status:
            print(f"Connected! Graph has {status.get('node_count', 0)} nodes, {status.get('edge_count', 0)} edges")

        stage = self.client.get_stage()
        if stage:
            print(f"Developmental Stage: {stage.get('stage', 'Unknown')} - {stage.get('name', '')}")

        print()
        self.running = True
        return True

    def stop(self) -> None:
        """Stop the CORTEX."""
        self.client.stop()
        self.running = False

        # Print audit summary
        summary = get_audit_log().get_summary()
        print()
        print("=" * 50)
        print("  Session Summary")
        print("=" * 50)
        print(f"  Total queries: {summary['total']}")
        print(f"  Verified: {summary['verified']}")
        print(f"  Unverified: {summary['unverified']}")
        print(f"  Partial: {summary['partial']}")
        if summary['total'] > 0:
            print(f"  Verification rate: {summary['verification_rate']:.1%}")
        print("=" * 50)

    def query(self, user_input: str) -> HonestResponse:
        """
        Process a user query.

        This demonstrates the Honesty Protocol:
        1. Parse user input as hypothesis
        2. Query Core for verification
        3. Return FACTS / INFERENCES / UNKNOWN
        """
        response = HonestResponse()

        # Parse command
        parts = user_input.strip().split()
        if not parts:
            response.add_unknown("Empty query", "No query provided")
            return response

        command = parts[0].lower()

        if command == "lookup" and len(parts) >= 2:
            return self._handle_lookup(parts[1])
        elif command == "traverse" and len(parts) >= 2:
            try:
                depth = int(parts[2]) if len(parts) >= 3 else 3
            except ValueError:
                response.add_unknown(user_input, "Invalid depth value")
                return response
            return self._handle_traverse(parts[1], depth)
        elif command == "path" and len(parts) >= 3:
            return self._handle_path(parts[1], parts[2])
        elif command == "ingest" and len(parts) >= 4:
            return self._handle_ingest(parts[1], parts[2], " ".join(parts[3:]))
        elif command == "status":
            return self._handle_status()
        elif command == "stage":
            return self._handle_stage()
        else:
            response.add_unknown(user_input, "Unknown command or invalid syntax")
            return response

    def _handle_lookup(self, entity_id_str: str) -> HonestResponse:
        """Handle a lookup command."""
        try:
            entity_id = int(entity_id_str)
        except ValueError:
            response = HonestResponse()
            response.add_unknown(f"lookup {entity_id_str}", "Invalid entity ID")
            return response

        # Query Core
        result = self.client.lookup(entity_id)

        # Verify hypothesis using Honesty Protocol
        hypothesis = f"Entity {entity_id} exists in the graph"
        status, response = verify_hypothesis(hypothesis, result)

        return response

    def _handle_traverse(self, start_str: str, depth: int) -> HonestResponse:
        """Handle a traverse command."""
        try:
            start_node = int(start_str)
        except ValueError:
            response = HonestResponse()
            response.add_unknown(f"traverse {start_str}", "Invalid node ID")
            return response

        result = self.client.traverse(start_node, depth)
        hypothesis = f"Node {start_node} has connections within depth {depth}"
        status, response = verify_hypothesis(hypothesis, result)

        return response

    def _handle_path(self, start_str: str, end_str: str) -> HonestResponse:
        """Handle a path command."""
        try:
            start = int(start_str)
            end = int(end_str)
        except ValueError:
            response = HonestResponse()
            response.add_unknown(f"path {start_str} {end_str}", "Invalid node IDs")
            return response

        result = self.client.strongest_path(start, end)
        hypothesis = f"A path exists from {start} to {end}"
        status, response = verify_hypothesis(hypothesis, result)

        return response

    def _handle_ingest(self, entity_id_str: str, attribute: str, value: str) -> HonestResponse:
        """Handle an ingest command."""
        response = HonestResponse()

        try:
            entity_id = int(entity_id_str)
        except ValueError:
            response.add_unknown(f"ingest {entity_id_str}", "Invalid entity ID")
            return response

        # Remove quotes from value if present
        value = value.strip('"').strip("'")

        node_id = self.client.ingest_signal(entity_id, attribute, value)

        if node_id is not None:
            response.add_fact(
                f"Signal ingested: entity={entity_id}, attr={attribute}, value={value}",
                [node_id]
            )
        else:
            response.add_unknown(
                f"ingest {entity_id} {attribute}",
                "Failed to ingest signal"
            )

        return response

    def _handle_status(self) -> HonestResponse:
        """Handle a status command."""
        response = HonestResponse()
        status = self.client.get_status()

        if status:
            response.add_fact(
                f"Graph: {status.get('node_count', 0)} nodes, {status.get('edge_count', 0)} edges, {status.get('stable_edges', 0)} stable",
                []
            )
        else:
            response.add_unknown("status", "Could not retrieve status")

        return response

    def _handle_stage(self) -> HonestResponse:
        """Handle a stage command."""
        response = HonestResponse()
        stage = self.client.get_stage()

        if stage:
            response.add_fact(
                f"Stage {stage.get('stage', '?')}: {stage.get('name', '?')} ({stage.get('progress_percent', 0)}% to next)",
                []
            )
        else:
            response.add_unknown("stage", "Could not retrieve stage")

        return response

    def repl(self) -> None:
        """Run the interactive REPL."""
        print("Commands:")
        print("  lookup <entity_id>         - Look up an entity")
        print("  traverse <node_id> [depth] - Traverse from node")
        print("  path <start> <end>         - Find strongest path")
        print("  ingest <id> <attr> <value> - Ingest a signal")
        print("  status                     - Show graph status")
        print("  stage                      - Show developmental stage")
        print("  audit                      - Show audit summary")
        print("  help                       - Show this help")
        print("  quit                       - Exit")
        print()

        while self.running:
            try:
                user_input = input("cortex> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("quit", "exit", "q"):
                    break

                if user_input.lower() == "help":
                    self.repl_help()
                    continue

                if user_input.lower() == "audit":
                    self.show_audit()
                    continue

                # Process query and show result
                response = self.query(user_input)
                print()
                print(response.to_text())
                print()

            except KeyboardInterrupt:
                print("\nInterrupted")
                break
            except EOFError:
                break

    def repl_help(self) -> None:
        """Show REPL help."""
        print()
        print("CORTEX Commands:")
        print("  lookup <entity_id>         - Look up an entity")
        print("  traverse <node_id> [depth] - Traverse from node")
        print("  path <start> <end>         - Find strongest path")
        print("  ingest <id> <attr> <value> - Ingest a signal")
        print("  status                     - Show graph status")
        print("  stage                      - Show developmental stage")
        print("  audit                      - Show audit summary")
        print("  help                       - Show this help")
        print("  quit                       - Exit")
        print()

    def show_audit(self) -> None:
        """Show audit log summary."""
        summary = get_audit_log().get_summary()
        print()
        print("Audit Summary:")
        print(f"  Total queries: {summary['total']}")
        print(f"  Verified: {summary['verified']}")
        print(f"  Unverified: {summary['unverified']}")
        print(f"  Partial: {summary['partial']}")
        if summary['total'] > 0:
            print(f"  Verification rate: {summary['verification_rate']:.1%}")
        print()


if __name__ == "__main__":
    from .cli import main
    main()
