"""
Kremis CORTEX - Honest AGI Layer

Provides the Honesty Protocol implementation for interacting
with Kremis Core via HTTP REST API.

Example:
    from kremis_cortex import KremisClient, Cortex

    # Direct client usage
    client = KremisClient()
    if client.start():
        result = client.lookup(entity_id=1)
        client.stop()

    # Interactive REPL
    cortex = Cortex()
    if cortex.start():
        cortex.repl()
        cortex.stop()
"""

from .client import (
    KremisClient,
    AsyncKremisClient,
    GroundedResult,
    Artifact,
    QueryResult,
    DEFAULT_BASE_URL,
)
from .cortex import Cortex
from .honesty_protocol import (
    HonestResponse,
    Fact,
    Inference,
    Unknown,
    VerificationStatus,
    AuditLog,
    verify_hypothesis,
    get_audit_log,
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "KremisClient",
    "AsyncKremisClient",
    "GroundedResult",
    "Artifact",
    "QueryResult",
    "DEFAULT_BASE_URL",
    # Cortex
    "Cortex",
    # Honesty Protocol
    "HonestResponse",
    "Fact",
    "Inference",
    "Unknown",
    "VerificationStatus",
    "AuditLog",
    "verify_hypothesis",
    "get_audit_log",
]
