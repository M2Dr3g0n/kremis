# NOTE: This example demonstrates the Honesty Protocol format.
# It does not require a running Kremis server.
# For examples using a live server, see the kremis_cortex.client module.

#!/usr/bin/env python3
"""
Example: Fact Retrieval

Demonstrates pure graph traversal - retrieving verified facts from the Core.

Per ROADMAP.md Section 10.5.5:
- Fact retrieval (pure graph traversal)
"""

from kremis_cortex import HonestResponse


def demo_fact_retrieval():
    """
    Demonstrate fact retrieval from the graph.

    In a real scenario, this would query the Core and get verified facts.
    This demo shows the expected output format.
    """
    print("=" * 50)
    print("  Example: Fact Retrieval")
    print("  Pure Graph Traversal Demo")
    print("=" * 50)
    print()

    # Simulate verified facts from Core
    response = HonestResponse()

    # These would come from actual Core queries
    response.add_fact(
        "Alice is known to the system",
        evidence_path=[1]  # NodeId
    )
    response.add_fact(
        "Alice knows Bob",
        evidence_path=[1, 2]  # Path from Alice to Bob
    )
    response.add_fact(
        "Alice and Bob share context 'Project X'",
        evidence_path=[1, 5, 2]  # Through shared node
    )

    print("Query: 'What do we know about Alice?'")
    print()
    print(response.to_text())
    print()
    print("Note: All facts are backed by graph evidence.")
    print("      Each fact shows the node path that supports it.")


if __name__ == "__main__":
    demo_fact_retrieval()
