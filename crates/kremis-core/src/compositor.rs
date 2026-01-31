//! # Compositor Module
//!
//! Output assembly protocol for Kremis CORE.
//!
//! Per ROADMAP.md Section 5.2.2:
//! - Output raw structure only
//! - No natural language generation
//! - No formatting logic in the Core
//! - Return `Option<Artifact>` for traversal results

use crate::graph::{Graph, GraphStore};
use crate::{Artifact, EdgeWeight, NodeId};

/// The Compositor handles output assembly from the graph.
///
/// Per AGENTS.md Section 3.3, the Compositor:
/// - Traverses the graph from active nodes
/// - Extracts paths or subgraphs
/// - Assembles Graph Artifacts
/// - Does NOT generate language, text, or meaning
pub struct Compositor;

impl Compositor {
    /// Compose an artifact by traversing from a starting node.
    ///
    /// Returns `None` if the node doesn't exist.
    pub fn compose(graph: &Graph, start: NodeId, depth: usize) -> Option<Artifact> {
        graph.traverse(start, depth)
    }

    /// Compose an artifact with weight filtering.
    ///
    /// Only includes edges with weight >= min_weight.
    pub fn compose_filtered(
        graph: &Graph,
        start: NodeId,
        depth: usize,
        min_weight: EdgeWeight,
    ) -> Option<Artifact> {
        graph.traverse_filtered(start, depth, min_weight)
    }

    /// Extract a path between two nodes.
    ///
    /// Uses strongest_path algorithm (maximizes edge weights).
    pub fn extract_path(graph: &Graph, start: NodeId, end: NodeId) -> Option<Artifact> {
        let path = graph.strongest_path(start, end)?;

        // Collect edges along the path
        let mut subgraph = Vec::new();
        for window in path.windows(2) {
            let from = window[0];
            let to = window[1];
            if let Some(weight) = graph.get_edge(from, to) {
                subgraph.push((from, to, weight));
            }
        }

        Some(Artifact::with_subgraph(path, subgraph))
    }

    /// Find common connections between multiple nodes.
    ///
    /// Returns an artifact containing the intersection nodes.
    pub fn find_intersection(graph: &Graph, nodes: &[NodeId]) -> Artifact {
        let common = graph.intersect(nodes);
        Artifact::with_path(common)
    }

    /// Extract a related subgraph from a starting point.
    pub fn related_context(graph: &Graph, start: NodeId, depth: usize) -> Option<Artifact> {
        graph.related_subgraph(start, depth)
    }
}

// =============================================================================
// TESTS
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::GraphStore;
    use crate::EntityId;

    #[test]
    fn compose_returns_none_for_missing_node() {
        let graph = Graph::new();
        let result = Compositor::compose(&graph, NodeId(999), 5);
        assert!(result.is_none());
    }

    #[test]
    fn compose_returns_artifact_for_existing_node() {
        let mut graph = Graph::new();
        let node = graph.insert_node(EntityId(1));

        let result = Compositor::compose(&graph, node, 1);
        assert!(result.is_some());
        assert!(!result.as_ref().map(|a| a.path.is_empty()).unwrap_or(true));
    }

    #[test]
    fn extract_path_finds_route() {
        let mut graph = Graph::new();
        let a = graph.insert_node(EntityId(1));
        let b = graph.insert_node(EntityId(2));
        let c = graph.insert_node(EntityId(3));

        graph.insert_edge(a, b, EdgeWeight::new(10));
        graph.insert_edge(b, c, EdgeWeight::new(10));

        let artifact = Compositor::extract_path(&graph, a, c);
        assert!(artifact.is_some());

        let path = artifact.as_ref().map(|a| &a.path);
        assert_eq!(path, Some(&vec![a, b, c]));
    }

    #[test]
    fn find_intersection_returns_common_neighbors() {
        let mut graph = Graph::new();
        let a = graph.insert_node(EntityId(1));
        let b = graph.insert_node(EntityId(2));
        let common = graph.insert_node(EntityId(100));

        graph.insert_edge(a, common, EdgeWeight::new(1));
        graph.insert_edge(b, common, EdgeWeight::new(1));

        let artifact = Compositor::find_intersection(&graph, &[a, b]);
        assert_eq!(artifact.path, vec![common]);
    }
}
