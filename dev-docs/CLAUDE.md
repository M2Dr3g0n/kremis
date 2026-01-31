# Kremis AI Context

> **Kremis** is a minimal, deterministic graph-based cognitive substrate.
> No output without a supporting graph path. The Core is CLOSED by design.

## Tech Stack

- **Language:** Rust (Stable, Edition 2021)
- **Core Storage:** `redb` (Embedded ACID Database)
- **Serialization:** `postcard` (canonical exports), `serde`
- **HTTP:** `axum` 0.8.x
- **CLI:** `clap` 4.x

## Common Commands

```bash
cargo build --workspace
cargo test --workspace
cargo clippy --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
cargo run -p kremis -- --help
cargo run -p kremis -- server
```

## Critical Constraints

- No `HashMap`/`HashSet` in Core (use `BTreeMap`/`BTreeSet`)
- No floating-point arithmetic in Core
- No randomness (`rand`, `uuid`) in Core
- No AI/ML algorithms in Core
- No `petgraph`

## Project Structure

```
kremis/
├── Cargo.toml              # Workspace Root
├── crates/
│   └── kremis-core/         # THE LOGIC (Lib) - Graph engine
│       └── src/
│           ├── lib.rs
│           ├── types/       # Core types (EntityId, Signal, etc.)
│           ├── graph.rs     # Deterministic graph engine
│           ├── formats/     # Persistence and serialization
│           ├── system/      # Stage assessment (S0-S3)
│           ├── storage/     # redb backend
│           └── ...
├── apps/
│   └── kremis/              # THE BINARY (Bin) - Server + CLI
│       └── src/
│           ├── main.rs
│           ├── api/         # HTTP REST API (axum)
│           └── cli/         # CLI commands (clap)
├── dev-docs/                # Documentation
│   ├── CLAUDE.md            # This file
│   └── ROADMAP.md           # Implementation status
├── docs/
│   ├── API.md               # HTTP API docs
│   └── CLI.md               # CLI docs
└── _archive/                # Archived components (SDK, Cortex, old docs)
```

## Workspace Members

| Crate | Type | Description |
|-------|------|-------------|
| `kremis-core` | lib | Deterministic graph engine |
| `kremis` (apps/) | bin | HTTP server + CLI |

## When Modifying Code

1. Run tests: `cargo test --workspace`
2. Update ROADMAP.md if completing/starting phases
3. Same input must produce same output (determinism)

---

**Last Updated:** 2026-01-30
**Version:** 0.1.0
