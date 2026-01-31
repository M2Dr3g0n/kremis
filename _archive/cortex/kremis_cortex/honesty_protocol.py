"""
Honesty Protocol - Verification logic for CORTEX outputs.

Per ROADMAP.md Section 10.5.4:
- MANDATORY: Every inference MUST be validated by Core query
- Implement fallback: if Core returns None, mark as "Unverified"
- Log all hypothesis-verification cycles for audit
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD: int = 70
LOW_CONFIDENCE_THRESHOLD: int = 50


class VerificationStatus(Enum):
    """Status of a verified claim."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTIAL = "partial"


@dataclass
class Fact:
    """A fact backed by graph evidence."""
    statement: str
    evidence_path: list[int]

    def __str__(self) -> str:
        path_str = " -> ".join(str(n) for n in self.evidence_path) if self.evidence_path else "no path"
        return f"[FACT] {self.statement} [path: {path_str}]"


@dataclass
class Inference:
    """An inference with confidence score."""
    statement: str
    confidence: int  # 0-100
    reasoning: str

    def __str__(self) -> str:
        return f"[INFERENCE] {self.statement} [{self.confidence}% confidence]"

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= HIGH_CONFIDENCE_THRESHOLD

    @property
    def is_low_confidence(self) -> bool:
        return self.confidence < LOW_CONFIDENCE_THRESHOLD


@dataclass
class Unknown:
    """An unknown with explanation."""
    query: str
    explanation: str

    def __str__(self) -> str:
        return f"[UNKNOWN] {self.query}: {self.explanation}"


@dataclass
class HonestResponse:
    """
    Complete honest response with FACTS / INFERENCES / UNKNOWN.

    Per ROADMAP.md Section 11.8.1, all output MUST use this structure.
    """
    facts: list[Fact] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    unknowns: list[Unknown] = field(default_factory=list)

    def add_fact(self, statement: str, evidence_path: list[int]) -> None:
        self.facts.append(Fact(statement, evidence_path))

    def add_inference(self, statement: str, confidence: int, reasoning: str) -> None:
        confidence = max(0, min(100, confidence))
        self.inferences.append(Inference(statement, confidence, reasoning))

    def add_unknown(self, query: str, explanation: str) -> None:
        self.unknowns.append(Unknown(query, explanation))

    def is_empty(self) -> bool:
        return not self.facts and not self.inferences and not self.unknowns

    def to_text(self) -> str:
        """Format as the standard honest output template."""
        lines = []
        lines.append("+-------------------------------------+")
        lines.append("| FACTS (Extracted from Core)        |")

        if not self.facts:
            lines.append("| - (none)                           |")
        else:
            for fact in self.facts:
                lines.append(f"| - {fact}")

        lines.append("+-------------------------------------+")
        lines.append("| INFERENCES (CORTEX deductions)     |")

        if not self.inferences:
            lines.append("| - (none)                           |")
        else:
            for inf in self.inferences:
                lines.append(f"| - {inf}")

        lines.append("+-------------------------------------+")
        lines.append("| UNKNOWN (Core returned None)       |")

        if not self.unknowns:
            lines.append("| - (none)                           |")
        else:
            for unk in self.unknowns:
                lines.append(f"| - {unk}")

        lines.append("+-------------------------------------+")

        return "\n".join(lines)


@dataclass
class VerificationCycle:
    """A single hypothesis-verification cycle for audit."""
    timestamp: datetime
    hypothesis: str
    query_type: str
    core_response: Any
    status: VerificationStatus
    evidence_path: list[int]


class AuditLog:
    """
    Audit log for all hypothesis-verification cycles.

    Per ROADMAP.md Section 10.5.4:
    - Log all hypothesis-verification cycles for audit
    """

    def __init__(self):
        self.cycles: list[VerificationCycle] = []
        self._lock = threading.Lock()

    def log(
        self,
        hypothesis: str,
        query_type: str,
        core_response: Any,
        status: VerificationStatus,
        evidence_path: list[int] | None = None,
    ) -> None:
        """Log a verification cycle."""
        with self._lock:
            self.cycles.append(VerificationCycle(
                timestamp=datetime.now(),
                hypothesis=hypothesis,
                query_type=query_type,
                core_response=core_response,
                status=status,
                evidence_path=evidence_path or [],
            ))

    def get_summary(self) -> dict:
        """Get summary statistics."""
        with self._lock:
            verified = sum(1 for c in self.cycles if c.status == VerificationStatus.VERIFIED)
            unverified = sum(1 for c in self.cycles if c.status == VerificationStatus.UNVERIFIED)
            partial = sum(1 for c in self.cycles if c.status == VerificationStatus.PARTIAL)

            return {
                "total": len(self.cycles),
                "verified": verified,
                "unverified": unverified,
                "partial": partial,
                "verification_rate": verified / len(self.cycles) if self.cycles else 0.0,
            }

    def clear(self) -> None:
        """Clear all cycles."""
        with self._lock:
            self.cycles.clear()


# Global audit log
_audit_log = AuditLog()


def get_audit_log() -> AuditLog:
    """Get the global audit log."""
    return _audit_log


def verify_hypothesis(hypothesis: str, core_result: Any) -> tuple[VerificationStatus, HonestResponse]:
    """
    Verify a hypothesis against Core result.

    Per ROADMAP.md Section 10.5.4:
    - MANDATORY: Every inference MUST be validated by Core query
    - If Core returns None, mark as "Unverified"

    Returns:
        Tuple of (status, response)
    """
    response = HonestResponse()

    if core_result is None:
        # Core returned None - mark as unverified
        response.add_unknown(hypothesis, "No supporting structure in graph")
        status = VerificationStatus.UNVERIFIED
    elif core_result.verified:
        # Fully verified
        response.add_fact(hypothesis, core_result.evidence_path)
        status = VerificationStatus.VERIFIED
    else:
        # Partial verification (low confidence)
        response.add_inference(
            hypothesis,
            core_result.confidence,
            f"Partial evidence with {core_result.confidence}% confidence"
        )
        status = VerificationStatus.PARTIAL

    # Log the cycle
    _audit_log.log(
        hypothesis=hypothesis,
        query_type="verify",
        core_response=core_result,
        status=status,
        evidence_path=core_result.evidence_path if core_result else [],
    )

    return status, response
