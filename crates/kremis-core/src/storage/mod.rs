//! # Storage Module
//!
//! Scalable storage for disk-backed graph operations using redb.
//!
//! Uses redb embedded database for:
//! - ACID transactions
//! - Crash safety (copy-on-write B-trees)
//! - MVCC (concurrent readers, single writer)

mod redb_graph;

pub use redb_graph::RedbGraph;
