# ROADMAP.md - Kremis Implementation Plan

> **STATUS:** PHASE 7 - SIMPLIFICATION (COMPLETE)

This document tracks the execution plan for Kremis.

---

## Legend

- COMPLETED: Verified and merged.
- IN PROGRESS: Currently under active development.
- PENDING: Planned/Designed but not started.

---

## Phase 0: Foundation (COMPLETED)

- Cargo workspace, CI/CD pipelines, strict linting.
- Core types: `EntityId`, `Signal`, `Artifact` in `kremis-core/src/types/`.
- Determinism: `std`-only logic (no `rand`, no `float`), `BTreeMap` enforcement.

---

## Phase 1: Graph Engine (COMPLETED)

- `Node` and `Edge` structs with `i64` weights, adjacency via `BTreeMap`.
- `redb` ACID storage with `GraphStore` trait.
- Canonical export/import via `postcard` in `kremis-core/src/export.rs`.
- LRU Cache with deterministic BTreeMap ordering in `kremis-core/src/cache.rs`.

---

## Phase 2: I/O Layer (COMPLETED)

- Ingestor (RX): Signal validation and deduplication in `kremis-core/src/ingestor.rs`.
- Compositor (TX): Artifact assembly in `kremis-core/src/compositor.rs`.
- HTTP API: REST server in `apps/kremis/src/api/`.
- CLI: Commands in `apps/kremis/src/cli/`.

---

## Phase 3: Traversal & Querying (COMPLETED)

- BFS/DFS with depth limits.
- `intersect(nodes)`, `strongest_path(start, end)`, `related_subgraph(start, depth)`.

---

## Phase 4: Honesty & Stages (COMPLETED)

- Honesty Protocol: "Reality Check" loop in `kremis-core/src/grounding.rs`.
- Stage Assessment in `kremis-core/src/system/stage.rs` (S0-S3).

---

## Phase 5: Verification (COMPLETED)

- Determinism tests, property-based testing with `proptest`.
- Security audit: no `unsafe`, all input validated.
- CLI: `server`, `status`, `stage`, `ingest`, `query`, `export`, `import`, `init`.
- HTTP: `/signal`, `/query`, `/status`, `/stage`, `/export`, `/health`.

---

## Phase 6: Consolidation (COMPLETED)

- Migrated from federated micro-crates to monolith.
- Types merged into `kremis-core/src/types/`.
- Single binary in `apps/kremis`.

---

## Phase 7: Simplification (COMPLETED)

- Archived `kremis-sdk` (no active plugins).
- Archived `cortex/` Python layer.
- Consolidated dev-docs from 6+ files to 2 (CLAUDE.md + ROADMAP.md).
- Removed CI overhead: cargo-deny, coverage, MSRV check, Python CI.
- Removed `reqwest` workspace dependency (SDK-only).

---

## Validation Tiers

- **T0:** Signal Integrity (input == output bytes).
- **T1:** Deterministic Edge Creation (same input = same edges).
- **T2:** Single-Hop Traversal (correct adjacent nodes).
- **T3:** Multi-Hop Traversal (deterministic complex paths).

---

## Current Workspace

| Crate | Type | Description |
|-------|------|-------------|
| `kremis-core` | lib | Deterministic graph engine |
| `kremis` (apps/) | bin | HTTP server + CLI |

## Approved Crates

### Core
| Crate | Purpose |
|-------|---------|
| `serde` 1.x | Serialization |
| `thiserror` 2.x | Error derive |
| `redb` 3.x | ACID database |
| `postcard` 1.x | Canonical binary format |

### App
| Crate | Purpose |
|-------|---------|
| `clap` 4.x | CLI |
| `serde_json` 1.x | JSON I/O |
| `tokio` 1.x | Async runtime |
| `axum` 0.8.x | HTTP server |
| `tracing` 0.1.x | Logging |
| `tower-http` 0.6.x | HTTP middleware |
| `base64` 0.22.x | Base64 encoding |

---

**Last Updated:** 2026-01-30
**Version:** 0.1.0
