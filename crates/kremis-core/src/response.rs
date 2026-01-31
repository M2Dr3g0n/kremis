//! # Response Module
//!
//! Structured, transparent response format for honest output.
//!
//! Per ROADMAP.md Section 11.8:
//! - Every fact includes source path in graph
//! - Every inference includes confidence percentage
//! - Every "unknown" explains what structure was missing
//! - No silent gap-filling or hallucination

use crate::NodeId;
use serde::{Deserialize, Serialize};

/// A fact backed by graph evidence.
///
/// Facts are statements that are directly supported by
/// the graph structure. They include the evidence path.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Fact {
    /// The factual statement.
    pub statement: String,
    /// The evidence path in the graph (nodes traversed).
    pub evidence_path: Vec<NodeId>,
}

impl Fact {
    /// Create a new fact with evidence.
    #[must_use]
    pub fn new(statement: impl Into<String>, evidence_path: Vec<NodeId>) -> Self {
        Self {
            statement: statement.into(),
            evidence_path,
        }
    }

    /// Check if this fact has supporting evidence.
    #[must_use]
    pub fn has_evidence(&self) -> bool {
        !self.evidence_path.is_empty()
    }
}

/// An inference with confidence score.
///
/// Inferences are deductions made by the CORTEX layer.
/// They include a confidence score (0-100) and reasoning.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Inference {
    /// The inferred statement.
    pub statement: String,
    /// Confidence score from 0 to 100.
    pub confidence: u8,
    /// Reasoning for the inference.
    pub reasoning: String,
}

impl Inference {
    /// Create a new inference.
    #[must_use]
    pub fn new(statement: impl Into<String>, confidence: u8, reasoning: impl Into<String>) -> Self {
        Self {
            statement: statement.into(),
            confidence: confidence.min(100),
            reasoning: reasoning.into(),
        }
    }

    /// Check if this inference is high confidence (>= 70).
    #[must_use]
    pub fn is_high_confidence(&self) -> bool {
        self.confidence >= 70
    }

    /// Check if this inference is low confidence (< 50).
    #[must_use]
    pub fn is_low_confidence(&self) -> bool {
        self.confidence < 50
    }
}

/// An unknown with explanation.
///
/// Unknowns are questions that could not be answered.
/// They include an explanation of what was missing.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Unknown {
    /// The original query that could not be answered.
    pub query: String,
    /// Explanation of what structure was missing.
    pub explanation: String,
}

impl Unknown {
    /// Create a new unknown.
    #[must_use]
    pub fn new(query: impl Into<String>, explanation: impl Into<String>) -> Self {
        Self {
            query: query.into(),
            explanation: explanation.into(),
        }
    }
}

/// The complete honest response.
///
/// Contains FACTS, INFERENCES, and UNKNOWNS separated clearly.
/// Per ROADMAP.md Section 11.8.1, all output must use this structure.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HonestResponse {
    /// Facts extracted from the Core graph.
    pub facts: Vec<Fact>,
    /// Inferences made by the CORTEX.
    pub inferences: Vec<Inference>,
    /// Unknowns (Core returned None).
    pub unknowns: Vec<Unknown>,
}

impl HonestResponse {
    /// Create an empty honest response.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a fact to the response.
    pub fn add_fact(&mut self, fact: Fact) {
        self.facts.push(fact);
    }

    /// Add an inference to the response.
    pub fn add_inference(&mut self, inference: Inference) {
        self.inferences.push(inference);
    }

    /// Add an unknown to the response.
    pub fn add_unknown(&mut self, unknown: Unknown) {
        self.unknowns.push(unknown);
    }

    /// Check if the response has any content.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.facts.is_empty() && self.inferences.is_empty() && self.unknowns.is_empty()
    }

    /// Format as plain text with the standard template.
    #[must_use]
    pub fn to_text(&self) -> String {
        let mut output = String::new();

        output.push_str("┌─────────────────────────────────────┐\n");
        output.push_str("│ FACTS (Extracted from Core)        │\n");

        if self.facts.is_empty() {
            output.push_str("│ - (none)                           │\n");
        } else {
            for fact in &self.facts {
                let path_str = if fact.evidence_path.is_empty() {
                    String::from("no path")
                } else {
                    fact.evidence_path
                        .iter()
                        .map(|n| n.0.to_string())
                        .collect::<Vec<_>>()
                        .join("→")
                };
                output.push_str(&format!("│ - {} [path: {}]\n", fact.statement, path_str));
            }
        }

        output.push_str("├─────────────────────────────────────┤\n");
        output.push_str("│ INFERENCES (Cortex deductions)     │\n");

        if self.inferences.is_empty() {
            output.push_str("│ - (none)                           │\n");
        } else {
            for inf in &self.inferences {
                output.push_str(&format!(
                    "│ - {} [{}% confidence]\n",
                    inf.statement, inf.confidence
                ));
            }
        }

        output.push_str("├─────────────────────────────────────┤\n");
        output.push_str("│ UNKNOWN (Core returned None)       │\n");

        if self.unknowns.is_empty() {
            output.push_str("│ - (none)                           │\n");
        } else {
            for unk in &self.unknowns {
                output.push_str(&format!("│ - {}: {}\n", unk.query, unk.explanation));
            }
        }

        output.push_str("└─────────────────────────────────────┘\n");

        output
    }
}

// =============================================================================
// TESTS
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fact_creation() {
        let fact = Fact::new("Alice knows Bob", vec![NodeId(1), NodeId(2)]);
        assert_eq!(fact.statement, "Alice knows Bob");
        assert!(fact.has_evidence());
    }

    #[test]
    fn inference_confidence() {
        let high = Inference::new("likely related", 85, "dense graph");
        let low = Inference::new("might be related", 30, "sparse graph");

        assert!(high.is_high_confidence());
        assert!(!high.is_low_confidence());
        assert!(!low.is_high_confidence());
        assert!(low.is_low_confidence());
    }

    #[test]
    fn unknown_creation() {
        let unknown = Unknown::new("What is X?", "No entity named X found");
        assert_eq!(unknown.query, "What is X?");
    }

    #[test]
    fn honest_response_building() {
        let mut response = HonestResponse::new();
        assert!(response.is_empty());

        response.add_fact(Fact::new("fact1", vec![]));
        response.add_inference(Inference::new("inf1", 80, "reason"));
        response.add_unknown(Unknown::new("q1", "not found"));

        assert!(!response.is_empty());
        assert_eq!(response.facts.len(), 1);
        assert_eq!(response.inferences.len(), 1);
        assert_eq!(response.unknowns.len(), 1);
    }

    #[test]
    fn to_text_format() {
        let mut response = HonestResponse::new();
        response.add_fact(Fact::new("Alice is known", vec![NodeId(1)]));
        response.add_inference(Inference::new("Likely friends", 75, "shared edges"));
        response.add_unknown(Unknown::new("Charlie?", "not in graph"));

        let text = response.to_text();

        assert!(text.contains("FACTS"));
        assert!(text.contains("INFERENCES"));
        assert!(text.contains("UNKNOWN"));
        assert!(text.contains("Alice is known"));
        assert!(text.contains("75% confidence"));
        assert!(text.contains("Charlie?"));
    }
}
