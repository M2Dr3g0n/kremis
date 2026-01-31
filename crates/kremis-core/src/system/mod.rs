//! # System Module
//!
//! Stage assessment and system metrics.
//!
//! MIGRATED FROM: kremis-facet-system/src/stage.rs
//!
//! Per KREMIS.md Section 9: Developmental Stages (FACET - Capability Maturation)
//!
//! This module implements the reference pattern for stage-based capability gating.
//! The CORE does NOT implement stages - this is a FACET responsibility.
//! However, the stage ASSESSMENT logic is pure and deterministic, so it belongs
//! in kremis-core for the Sidecar architecture.

mod stage;

pub use stage::*;
