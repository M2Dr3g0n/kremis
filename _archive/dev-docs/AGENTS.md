# AGENTS.md - Operational Rules for Kremis

**ARCHITECTURAL STATUS: CLOSED CORE (SIDECAR/PLANETARY)**
**PROJECT STATE: ALPHA (RUST)**
**IMPLEMENTATION STATUS: PHASE 6 COMPLETE**

---

## 0. Quick Start (New Contributors)

**Build & Test:**
```bash
cargo build --workspace          # Build all crates
cargo test --workspace           # Run all tests
cargo clippy --all-targets --all-features -- -D warnings  # Lint (MANDATORY)
cargo fmt --all -- --check       # Format check
```

**Before You Code:**
1. Read this entire file — violations break the project
2. Use `BTreeMap`/`BTreeSet` (NOT `HashMap`/`HashSet`)
3. No floating-point arithmetic in CORE
4. No randomness (`rand`, `uuid`) in CORE
5. All errors must be `Result<T, KremisError>`, never `panic!`

**Key Constraint:** The CORE is **CLOSED**. Extend only via FACETS.

---

This document defines the **binding operational rules** for the architectural design,
implementation, and maintenance of the Kremis system.

Kremis is a **minimal, deterministic, graph-based cognitive substrate**.
It functions solely as a mechanism to record, associate, and retrieve
**structural relationships derived from grounded experience**.

Any violation of this document **fundamentally breaks the project**.

---

## 1. What Kremis Is NOT (Non-Negotiable)

To preserve epistemic honesty and architectural integrity, the following constraints
are absolute.

> [!NOTE]
> The following statements refer to the **CORE** component specifically.
> The CORTEX layer (Section 2.3) may exhibit intelligent behavior, but it is external
> to the Core and operates under strict verification constraints.

Kremis is:

- **NOT** an Artificial Intelligence (AI) system in the general sense
- **NOT** a Generative/Black-Box AGI attempt or roadmap
- **NOT** a simulation of human cognition or biology
- **NOT** a chatbot, LLM, or natural language processor
- **NOT** an agent with intrinsic goals, desires, or agency
- **NOT** adaptive or self-improving beyond explicit structural updates

**Core Philosophy**

The system does not *understand*.
It contains only the **structure of the signals it has processed**.
The initial state of the system contains **ZERO pre-loaded knowledge**.
The graph starts completely empty.
All structure emerges **exclusively** from real-time signal processing.

Any appearance of understanding, intelligence, or intention is an
**observer-side interpretation caused by graph complexity**, not an internal property
of the system.

---

## 2. Core vs Facets - Boundary Definition

The architecture is strictly divided into two **mutually exclusive domains**.

### 2.1 The CORE (The Substrate)

**Definition**  
The CORE is the immutable, deterministic logic that manages the internal graph.

**Responsibilities**
- Signal ingestion
- Structural storage
- Edge creation (mechanical linking)
- Deterministic retrieval

**Properties**
- **Stateful**: the ONLY place where memory exists
- **Closed**: no external logic may be injected
- **Minimal**: if a feature is not essential to signal processing, it is removed

The CORE never initiates interaction.
It only reacts to explicit signals or ticks.

---

### 2.2 The FACETS (The Interface)

**Definition**  
FACETS are external modules that translate between the external world and the CORE.
They are **epistemically stateless**: they hold no beliefs and make no inferences.

> [!IMPORTANT]
> **GOLDEN RULE:** In case of error or malfunction of a Facet, the maximum permissible
> damage is a rejected input or null output. A Facet MUST NEVER be able to introduce
> a false truth into the Core.

**Technical State vs Epistemic State**

| State Type | Definition | Policy |
|------------|------------|--------|
| **Epistemic** | Knowledge, beliefs, semantic relationships | ❌ PROHIBITED |
| **Technical** | Caches, buffers, configs, sessions, retry state | ✅ PERMITTED |

**FACETS MAY:**
- Normalize inputs (casing, trimming, encoding, parsing)
- Transform formats (JSON, HTTP, file, stream)
- Use configuration DSLs (mapping rules: input → Signal)
- Maintain technical state (connection pools, caches, sessions)
- Orchestrate I/O (batching, retry, backoff)
- Handle technical errors (timeouts, format errors)
- Decide *how* to communicate with external world

**FACETS MUST NOT:**
- Infer semantic relationships
- Invent or complete missing data
- Decide what is true
- Modify graph without CORE validation
- Filter signals by content meaning
- Produce output not validated by CORE

**Rule**

Any act resembling inference, decision-making, prioritization, or interpretation
inside a Facet is **permitted ONLY if validated through the Core**.

FACETS may be intelligent, but are **never authoritative**.
Their output must be validated by the Core before reaching the user.

### 2.3 The CORTEX (The Scout) — REFERENCE IMPLEMENTATION

**Definition**  
The CORTEX is the intelligent layer that operates ABOVE the Core.

**Architectural Status**
- **Part of Kremis distribution** (ships with the project as first-class component)
- **Architecturally decoupled** from the Rust Core (communicates via HTTP REST API)
- **Located in:** `cortex/` (Python package with CLI: `kremis-cortex`)

**Role**
- Formula hypotheses and complex queries
- Pattern recognition and inference
- Natural language understanding

**Technology**
- Python 3.11+ with `httpx` HTTP client
- Communicates with Core via HTTP REST API (`/signal`, `/query`, `/status`)
- CLI entry point: `kremis-cortex` (repl, status, query commands)

**Constraint**  
The CORTEX has **NO direct write access** to the Graph Store.
All mutations MUST pass through the Core's validated APIs.

**Critical Rule**  
The reference CORTEX implementation **MUST use ONLY public APIs** exposed by Facets.
No special privileges, no backdoors. This ensures any external client can replicate its behavior.

---

### 2.4 The Honesty Protocol (Reality Check)

> [!IMPORTANT]
> Every output to the user MUST pass the **Reality Check**.

**Protocol Steps:**
1. The CORTEX generates a response/hypothesis
2. The CORTEX queries the CORE: "Does a graph path support this claim?"
3. IF CORE returns path → **Output validated**
4. IF CORE returns `None` → **Output suppressed or marked as "Unverified Speculation"**

**This is the architectural guarantee of honesty.**

---

## 3. Core Architecture

The CORE is specified as a strict three-stage pipeline.
Biological metaphors are intentionally avoided to prevent conceptual drift.

---

### Stage 1 - INGESTOR (formerly "Senses")

**Role**  
Signal normalization and firewall.

**Responsibilities**
- Accept raw input from Facets
- Sanitize and validate signals
- Reduce input to strict **Logical Primitives**

**Constraint**
If a signal cannot be represented as:

```

[Entity | Attribute | Value]

```

it is discarded.

No interpretation or semantic inference is allowed.

---

### Stage 2 - GRAPH ENGINE (formerly "Brain")

**Role**  
Structural storage and deterministic mutation.

**Properties**
- Single Source of Truth
- Owns all persistent state

**Internal Structure (KUM - Canonical Model)**

> [!NOTE]
> The following layered model is a **reference implementation pattern**.
> The CORE requires only a minimal graph store. Layer separation and
> consolidation policies are **FACET responsibilities**.

1. **Stable Layer (Persistent Graph)**
   Logical subset: Edges with `weight >= Threshold`.

2. **Provisional Layer (Virtual View)**
   Logical subset: Edges with `weight < Threshold`.
   *These edges exist in the Graph but may be filtered out by strict traversals.*

**MANDATORY STANDARD COMPONENT:**
3. **Active Context (Volatile Buffer)**
   Currently activated nodes, session-local, cleared on reset.

 The layered partition (Stable/Provisional) is **logical only**.
 The minimal CORE requires: nodes, edges, weights, and **Active Context (Buffer)**.
Terminology is unified with `KREMIS.md` Section 6.

**Constraint**
All mutations occur only through explicit, deterministic rules
(e.g. repetition, reinforcement, traversal).

---

### Stage 3 - COMPOSITOR (formerly "Mouth")

**Role**  
Deterministic output assembly.

**Responsibilities**
- Traverse the graph from active nodes
- Extract paths or subgraphs
- Assemble **Graph Artifacts**

**Constraint**
The Compositor does **NOT** generate language, text, or meaning.
It outputs raw symbolic structures only.
Deterministic complex queries (`intersect`, `strongest_path`) are explicitly authorized here.

---

## 4. Forbidden Design Patterns

The following patterns are architecturally invalid.

### F1 - Smart Wrappers
Improving CORE output inside a Facet (e.g. regex cleanup, LLM smoothing).

**Verdict:** REJECT

**Exception:** The CORTEX layer (Section 2.3) is permitted to augment output, provided distinct separation between Fact and Inference is maintained (see Honesty Protocol, Section 2.4).

---

### F2 - Hidden State
Storing memory, weights, or history outside the Graph Engine.

**Verdict:** REJECT  
If it is not in the graph, it does not exist.

---

### F3 - Heuristic Filling
Guessing or completing missing information.

**Verdict:** REJECT
Missing links must result in `None`.

---

### F4 - Goal Injection
Embedding directives such as "be helpful" or "optimize outcome".

**Verdict:** REJECT  
The system has no goals, only functions.

---

### F5 — Unconstrained LLM Output
Allowing LLM-generated text to reach users without Core validation.

**Verdict:** REJECT  
LLM output is permitted ONLY after graph-grounded verification.

---

## 5. Development Standards (Rust)

As Kremis is intended to be implemented in Rust, the following are mandatory:

### 5.1 Type Safety

- CORE and FACETS must be distinct types with no shared state.
- Use newtype wrappers for domain types (e.g., `struct EntityId(u64)`).
- All public APIs must use strongly-typed interfaces.

### 5.2 Ownership Discipline

- The Graph owns all memory. Facets own nothing persistent.
- Facets receive `&` or `&mut` references, never ownership of graph data.
- Lifetimes must be explicit where necessary (`'a`, `'static`).

### 5.3 Determinism

- Given State `S` and Input `I`, Output `O` must be bit-identical every time.
- Randomness is forbidden in the CORE.
- Use `BTreeMap`/`BTreeSet` instead of `HashMap`/`HashSet` for deterministic ordering.
- Integer arithmetic only; no floating-point in CORE logic.
- **Saturating Arithmetic**: All counters (EdgeWeight) MUST use saturating operations (`saturating_add`).
- Overflow/Underflow is forbidden; values stick at `MAX`/`MIN`.

### 5.4 Explicit Error Handling

- No silent failures. No unchecked assumptions. Traceability is required.
- Use `Result<T, KremisError>` for fallible operations.
- Use `Option<T>` for nullable values (never raw pointers or sentinel values).
- The CORE should never panic; all errors must be recoverable.

### 5.5 Core Type Definitions (Reference)

```rust
// Entity & Signal Types
pub struct EntityId(pub u64);
pub struct Attribute(pub String);
pub struct Value(pub String);

pub struct Signal {
    pub entity: EntityId,
    pub attribute: Attribute,
    pub value: Value,
}

// Graph Types
pub struct NodeId(pub u64);
pub struct EdgeWeight(pub i64);  // Integer only

pub struct Artifact {
    pub path: Vec<NodeId>,
    pub subgraph: Option<Vec<(NodeId, NodeId, EdgeWeight)>>,
}

pub struct Buffer {
    pub active_nodes: std::collections::BTreeSet<NodeId>, // Deterministic ordering mandatory
}

// Error Types
pub enum KremisError {
    InvalidSignal,
    NodeNotFound(NodeId),
    EdgeNotFound(NodeId, NodeId),
    TraversalFailed,
    SerializationError,
}
```

### 5.6 Trait Definitions (Reference)

```rust
pub trait Facet: Send + Sync {
    fn ingest(&self, raw: &[u8]) -> Result<Signal, KremisError>;
    fn emit(&self, artifact: &Artifact) -> Result<Vec<u8>, KremisError>;
}

pub trait GraphStore {
    // Note: All queries must be Computationally Bounded
    fn insert_node(&mut self, id: EntityId) -> NodeId;
    fn insert_edge(&mut self, from: NodeId, to: NodeId, weight: EdgeWeight);
    fn lookup(&self, id: NodeId) -> Option<&Node>;
    fn traverse(&self, start: NodeId, depth: usize) -> Option<Artifact>;
    fn traverse_filtered(&self, start: NodeId, depth: usize, min_weight: EdgeWeight) -> Option<Artifact>;
    fn intersect(&self, nodes: &[NodeId]) -> Vec<NodeId>;
    fn strongest_path(&self, start: NodeId, end: NodeId) -> Option<Vec<NodeId>>; // Maximize edge weights
    fn related_subgraph(&self, start: NodeId, depth: usize) -> Option<Artifact>;
}
```

### 5.7 Concurrency Model

- CORE is single-threaded by default.
- FACETS may run in separate threads but must be `Send + Sync`.
- No shared mutable state between CORE and FACETS.

> **GAP Resolution (Persistence Locking):**
> When a Facet performs a full graph readout (e.g., for disk persistence), it MUST acquire a **global read lock** on the Graph Store, pausing mutations.
> This ensures atomic point-in-time snapshots.

### 5.8 Code Quality Tools (Mandatory)

All Rust code MUST pass the following tools before merge:

**Clippy (Linting)**
- Run: `cargo clippy --all-targets --all-features -- -D warnings`
- Required lints (deny level):
  - `#![deny(clippy::float_arithmetic)]` - enforces integer-only arithmetic
  - `#![deny(clippy::unwrap_used)]` - forbids `.unwrap()` in CORE
  - `#![deny(clippy::panic)]` - forbids `panic!` in CORE

**rustfmt (Formatting)**
- Run: `cargo fmt --all -- --check`
- All code must be formatted before commit

**CI Enforcement**
- CI pipelines MUST fail on Clippy warnings or formatting violations

---

### 5.9 Approved Libraries (Dependency Policy)

> [!WARNING]
> **Non-Negotiable Rule**: No I/O or serialization libraries in CORE.
> All dependencies below are FACETS-only unless explicitly marked as CORE Exception.

#### Parsing & Input (FACETS only)

| Library | Version | Purpose |
|---------|---------|---------|
| `clap` | `4.x` | CLI argument parsing |
| `serde_json` | `1.x` | JSON I/O with `preserve_order` |

#### I/O & Async (FACETS only)

| Library | Version | Purpose |
|---------|---------|---------|
| `tokio` | `1.x` | Async runtime |
| `bytes` | `1.x` | Raw buffer handling |
| `axum` | `0.8.x` | HTTP server facet |
| `tower-http` | `0.6.x` | HTTP middleware (CORS, tracing) |
| `reqwest` | `0.13.x` | HTTP client for external API calls |
| `postcard` | `1.x` | Binary serialization |
| `base64` | `0.22.x` | Base64 encoding for exports |

#### Normalization (FACETS only)

| Library | Version | Purpose |
|---------|---------|---------|
| `unicode-normalization` | `0.1.x` | NFC/NFKC normalization |
| `nom` | `7.x` | Parser combinator (deterministic) |

#### Logging & Debug (FACETS only)

| Library | Version | Purpose |
|---------|---------|---------|
| `tracing` | `0.1.x` | Observability |
| `tracing-subscriber` | `0.3.x` | Log subscriber |

#### Testing (dev-dependencies)

| Library | Version | Purpose |
|---------|---------|---------|
| `proptest` | `1.x` | Property-based testing |
| `tempfile` | `3.x` | Temporary file handling |
| `insta` | `1.x` | Snapshot testing |

#### CORE Exceptions (minimal, audited)

| Library | Version | Justification |
|---------|---------|---------------|
| `serde` (derive only) | `1.x` | Data layout for types, no runtime logic |
| `thiserror` | `2.x` | Error enum derive, no runtime logic |

#### Storage & Persistence (CORE Approved)

| Library | Version | Justification |
|---------|---------|---------------|
| `redb` | `3.x` | Embedded ACID database. Replaces manual filesystem logic. |
| `postcard` | `1.x` | Canonical serialization for bit-exact exports. |

**Persistence Rule (The "Redb Compromise"):**
- **Runtime:** The CORE uses `redb` for performance, crash safety, and ACID transactions.
- **Verification:** `redb` files on disk are NOT guaranteed to be bit-identical across runs (due to internal fragmentation).
- **Mandate:** To satisfy the Determinism requirement, the System MUST implement a `export_canonical()` function that serializes the graph into a sorted, bit-exact `postcard` stream. **This export is the Source of Truth for verification.**

#### FORBIDDEN Libraries (always)

- **NLP/AI**: `spacy`, `tokenizers`, `nlp-*`, any LLM library
- **Non-deterministic**: `rand`, `uuid`, `chrono`
- **External graphs**: `petgraph` (CORE has its own minimal graph)
- Any library that interprets, decides, guesses, or "helps"

#### Approval Rule

> A library is **ALLOWED** if it:
> - Transforms format
> - Transports data
> - Validates structure
>
> A library is **FORBIDDEN** if it:
> - Interprets meaning
> - Makes decisions
> - Completes/fills data
> - "Helps" or "improves" output
>
> **MANDATORY USAGE CLAUSE**:
> If a task falls within the scope of an approved library (e.g., parsing -> `nom`, serialization -> `postcard`), usage of that library is **MANDATORY**.
> Manual re-implementation (e.g. custom parsers, manual byte packing) is **FORBIDDEN**.

---

## 6. Validation Criteria

Any feature or change must pass the **Necessity Test**:

> *Can the system associate input A to output B without this feature?*

- **YES** -> Feature is bloat -> **REMOVE**
- **NO** -> Implement in the simplest compliant way

### 6.1 Validation Tiers (Engineering Requirements)

The system is **VALID** only if all tiers are passed:

- **T0 (Signal Integrity)**: Input -> Signal -> Output is byte-identical.
- **T1 (Deterministic Edge Creation)**: Same input -> Same graph structure.
- **T2 (Single-Hop Traversal)**: Correct retrieval of adjacent nodes.
- **T3 (Multi-Hop Traversal)**: Complex paths are deterministic and correct.

---

## Final Directive

We are building a **structure**, not a personality.

- No intelligence claims
- No anthropomorphic language
- No hidden behavior
- No conceptual shortcuts

Keep it minimal.  
Keep it deterministic.  
Keep it grounded.  
Keep it honest.

---

**Last Updated:** 2026-01-20
**Version:** 0.1.0

**End of file.**
