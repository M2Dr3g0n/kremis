# NOTE: This example demonstrates the Honesty Protocol format.
# It does not require a running Kremis server.
# For examples using a live server, see the kremis_cortex.client module.

#!/usr/bin/env python3
"""
Example: Inference with High Confidence

Demonstrates inference supported by dense graph structure.

Per ROADMAP.md Section 10.5.5:
- Inference with high confidence (dense graph support)
"""

from kremis_cortex import HonestResponse


def demo_high_confidence_inference():
    """
    Demonstrate high-confidence inference.

    When the graph has dense connections supporting a claim,
    we can make inferences with high confidence.
    """
    print("=" * 50)
    print("  Example: High Confidence Inference")
    print("  Dense Graph Support Demo")
    print("=" * 50)
    print()

    response = HonestResponse()

    # Facts from Core
    response.add_fact(
        "Alice is on Team Engineering",
        evidence_path=[1, 10]
    )
    response.add_fact(
        "Bob is on Team Engineering",
        evidence_path=[2, 10]
    )
    response.add_fact(
        "Charlie is on Team Engineering",
        evidence_path=[3, 10]
    )
    response.add_fact(
        "Alice, Bob, and Charlie attended Meeting #42",
        evidence_path=[1, 20, 2, 20, 3]
    )

    # High confidence inference
    response.add_inference(
        "Alice and Bob likely collaborate frequently",
        confidence=85,  # High confidence due to multiple connections
        reasoning="Strong graph support: same team, shared meetings, 5 common edges"
    )

    print("Query: 'Do Alice and Bob work together?'")
    print()
    print(response.to_text())
    print()
    print("Note: High confidence (85%) due to dense graph connections.")
    print("      Multiple facts support this inference.")


if __name__ == "__main__":
    demo_high_confidence_inference()
