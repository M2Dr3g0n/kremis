# NOTE: This example demonstrates the Honesty Protocol format.
# It does not require a running Kremis server.
# For examples using a live server, see the kremis_cortex.client module.

#!/usr/bin/env python3
"""
Example: Honest Uncertainty

Demonstrates honest "I don't know" when graph is sparse.

Per ROADMAP.md Section 10.5.5:
- Honest uncertainty (sparse graph -> "I don't know")
"""

from kremis_cortex import HonestResponse


def demo_honest_uncertainty():
    """
    Demonstrate honest uncertainty.

    When the Core returns None (no supporting structure),
    we MUST mark the response as UNKNOWN.
    This is the key to "Honest AGI".
    """
    print("=" * 50)
    print("  Example: Honest Uncertainty")
    print("  'I Don't Know' Demo")
    print("=" * 50)
    print()

    response = HonestResponse()

    # Some facts we do know
    response.add_fact(
        "David exists in the system",
        evidence_path=[4]
    )

    # Unknowns - Core returned None
    response.add_unknown(
        "What team is David on?",
        "No team relationship found for entity 4"
    )
    response.add_unknown(
        "Does David know Alice?",
        "No path exists between nodes 4 and 1"
    )
    response.add_unknown(
        "What projects is David working on?",
        "No project associations in graph for entity 4"
    )

    print("Query: 'Tell me about David's work relationships'")
    print()
    print(response.to_text())
    print()
    print("=" * 50)
    print("  KEY PRINCIPLE: Honesty Protocol")
    print("=" * 50)
    print()
    print("  When Core returns None:")
    print("  X DO NOT guess or fill gaps")
    print("  X DO NOT hallucinate connections")
    print("  V DO say 'I don't know'")
    print("  V DO explain what's missing")
    print()
    print("  This is what makes Kremis an 'Honest AGI'.")


if __name__ == "__main__":
    demo_honest_uncertainty()
