"""
Tests for Honesty Protocol.

Tests the verification logic and HonestResponse structure.
"""

import pytest

from kremis_cortex.honesty_protocol import (
    VerificationStatus,
    Fact,
    Inference,
    Unknown,
    HonestResponse,
    VerificationCycle,
    AuditLog,
    get_audit_log,
    verify_hypothesis,
)


class TestFact:
    """Tests for Fact dataclass."""

    def test_fact_creation(self):
        """Test basic fact creation."""
        fact = Fact(statement="Alice exists", evidence_path=[1])
        assert fact.statement == "Alice exists"
        assert fact.evidence_path == [1]

    def test_fact_str_with_path(self):
        """Test fact string representation with path."""
        fact = Fact(statement="A knows B", evidence_path=[1, 2, 3])
        fact_str = str(fact)
        assert "[FACT]" in fact_str
        assert "A knows B" in fact_str
        assert "1 -> 2 -> 3" in fact_str

    def test_fact_str_empty_path(self):
        """Test fact string representation with empty path."""
        fact = Fact(statement="Orphan", evidence_path=[])
        fact_str = str(fact)
        assert "no path" in fact_str


class TestInference:
    """Tests for Inference dataclass."""

    def test_inference_creation(self):
        """Test basic inference creation."""
        inference = Inference(
            statement="A might know C",
            confidence=75,
            reasoning="Transitive relationship",
        )
        assert inference.statement == "A might know C"
        assert inference.confidence == 75
        assert inference.reasoning == "Transitive relationship"

    def test_inference_str(self):
        """Test inference string representation."""
        inference = Inference(statement="Test", confidence=85, reasoning="Test")
        inference_str = str(inference)
        assert "[INFERENCE]" in inference_str
        assert "85%" in inference_str

    def test_is_high_confidence(self):
        """Test high confidence check."""
        high = Inference(statement="High", confidence=70, reasoning="")
        low = Inference(statement="Low", confidence=69, reasoning="")
        assert high.is_high_confidence is True
        assert low.is_high_confidence is False

    def test_is_low_confidence(self):
        """Test low confidence check."""
        low = Inference(statement="Low", confidence=49, reasoning="")
        not_low = Inference(statement="Not low", confidence=50, reasoning="")
        assert low.is_low_confidence is True
        assert not_low.is_low_confidence is False


class TestUnknown:
    """Tests for Unknown dataclass."""

    def test_unknown_creation(self):
        """Test basic unknown creation."""
        unknown = Unknown(query="Who is X?", explanation="No data in graph")
        assert unknown.query == "Who is X?"
        assert unknown.explanation == "No data in graph"

    def test_unknown_str(self):
        """Test unknown string representation."""
        unknown = Unknown(query="Test query", explanation="Not found")
        unknown_str = str(unknown)
        assert "[UNKNOWN]" in unknown_str
        assert "Test query" in unknown_str
        assert "Not found" in unknown_str


class TestHonestResponse:
    """Tests for HonestResponse dataclass."""

    def test_empty_response(self):
        """Test empty response."""
        response = HonestResponse()
        assert response.is_empty() is True
        assert len(response.facts) == 0
        assert len(response.inferences) == 0
        assert len(response.unknowns) == 0

    def test_add_fact(self):
        """Test adding facts."""
        response = HonestResponse()
        response.add_fact("Alice exists", [1])
        assert len(response.facts) == 1
        assert response.facts[0].statement == "Alice exists"
        assert response.is_empty() is False

    def test_add_inference(self):
        """Test adding inferences."""
        response = HonestResponse()
        response.add_inference("Might be related", 65, "Weak connection")
        assert len(response.inferences) == 1
        assert response.inferences[0].confidence == 65

    def test_add_unknown(self):
        """Test adding unknowns."""
        response = HonestResponse()
        response.add_unknown("Who is X?", "No data")
        assert len(response.unknowns) == 1
        assert response.unknowns[0].query == "Who is X?"

    def test_to_text_empty(self):
        """Test text output for empty response."""
        response = HonestResponse()
        text = response.to_text()
        assert "FACTS" in text
        assert "INFERENCES" in text
        assert "UNKNOWN" in text
        assert "(none)" in text

    def test_to_text_with_content(self):
        """Test text output with content."""
        response = HonestResponse()
        response.add_fact("Alice exists", [1])
        response.add_inference("Might know Bob", 75, "Common context")
        response.add_unknown("Where is Carol?", "Not in graph")

        text = response.to_text()
        assert "[FACT]" in text
        assert "Alice exists" in text
        assert "[INFERENCE]" in text
        assert "75%" in text
        assert "[UNKNOWN]" in text
        assert "Carol" in text

    def test_multiple_entries(self):
        """Test multiple entries of each type."""
        response = HonestResponse()
        response.add_fact("Fact 1", [1])
        response.add_fact("Fact 2", [2])
        response.add_inference("Inference 1", 80, "Reason 1")
        response.add_inference("Inference 2", 60, "Reason 2")
        response.add_unknown("Unknown 1", "Explanation 1")

        assert len(response.facts) == 2
        assert len(response.inferences) == 2
        assert len(response.unknowns) == 1


class TestAuditLog:
    """Tests for AuditLog."""

    def test_empty_log(self):
        """Test empty audit log."""
        log = AuditLog()
        summary = log.get_summary()
        assert summary["total"] == 0
        assert summary["verification_rate"] == 0.0

    def test_log_verified(self):
        """Test logging verified cycles."""
        log = AuditLog()
        log.log(
            hypothesis="Test",
            query_type="lookup",
            core_response=None,
            status=VerificationStatus.VERIFIED,
            evidence_path=[1, 2],
        )
        summary = log.get_summary()
        assert summary["total"] == 1
        assert summary["verified"] == 1

    def test_log_unverified(self):
        """Test logging unverified cycles."""
        log = AuditLog()
        log.log(
            hypothesis="Test",
            query_type="lookup",
            core_response=None,
            status=VerificationStatus.UNVERIFIED,
        )
        summary = log.get_summary()
        assert summary["unverified"] == 1

    def test_log_partial(self):
        """Test logging partial cycles."""
        log = AuditLog()
        log.log(
            hypothesis="Test",
            query_type="lookup",
            core_response=None,
            status=VerificationStatus.PARTIAL,
        )
        summary = log.get_summary()
        assert summary["partial"] == 1

    def test_verification_rate(self):
        """Test verification rate calculation."""
        log = AuditLog()
        # 3 verified, 1 unverified = 75% rate
        for _ in range(3):
            log.log("", "", None, VerificationStatus.VERIFIED)
        log.log("", "", None, VerificationStatus.UNVERIFIED)

        summary = log.get_summary()
        assert summary["verification_rate"] == 0.75

    def test_clear(self):
        """Test clearing the log."""
        log = AuditLog()
        log.log("Test", "lookup", None, VerificationStatus.VERIFIED)
        assert log.get_summary()["total"] == 1
        log.clear()
        assert log.get_summary()["total"] == 0


class TestGlobalAuditLog:
    """Tests for global audit log."""

    def test_get_audit_log(self):
        """Test getting global audit log."""
        log = get_audit_log()
        assert isinstance(log, AuditLog)

    def test_global_log_persistence(self):
        """Test that global log is the same instance."""
        log1 = get_audit_log()
        log2 = get_audit_log()
        assert log1 is log2


class TestVerifyHypothesis:
    """Tests for verify_hypothesis function."""

    def test_verify_none_result(self):
        """Test verification with None result."""
        status, response = verify_hypothesis("Test hypothesis", None)
        assert status == VerificationStatus.UNVERIFIED
        assert len(response.unknowns) == 1
        assert response.unknowns[0].query == "Test hypothesis"

    def test_verify_verified_result(self, sample_grounded_result_verified):
        """Test verification with verified result."""
        status, response = verify_hypothesis(
            "Entity exists",
            sample_grounded_result_verified,
        )
        assert status == VerificationStatus.VERIFIED
        assert len(response.facts) == 1
        assert response.facts[0].statement == "Entity exists"

    def test_verify_partial_result(self, sample_grounded_result_partial):
        """Test verification with partial result."""
        status, response = verify_hypothesis(
            "Might be related",
            sample_grounded_result_partial,
        )
        assert status == VerificationStatus.PARTIAL
        assert len(response.inferences) == 1
        assert response.inferences[0].confidence == 65

    def test_verify_logs_to_audit(self, sample_grounded_result_verified):
        """Test that verification logs to audit."""
        log = get_audit_log()
        initial_count = log.get_summary()["total"]

        verify_hypothesis("Test", sample_grounded_result_verified)

        assert log.get_summary()["total"] == initial_count + 1


class TestVerificationStatus:
    """Tests for VerificationStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.UNVERIFIED.value == "unverified"
        assert VerificationStatus.PARTIAL.value == "partial"
