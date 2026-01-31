# Kremis – Architectural Overview & Manifesto

**Kremis** is a minimal, deterministic, grounded cognitive core intended to be implemented in **Rust**.

Kremis is a **Grounded Neuro-Symbolic architecture**.
The system separates **Intelligence** (generative/inferential) from **Truth** (structural/deterministic).

It aims to solve the hallucination problem through **mandatory topological verification**.

---

## 1. Architectural Status: CLOSED CORE (NON-NEGOTIABLE)

> **WARNING**
>
> The CORE architecture of Kremis is **strictly CLOSED**.

Kremis is defined by its **limitations**.
Any attempt to expand the CORE beyond its declared scope **breaks the project by definition**.

### Core Definition

The CORE is **specified as** a deterministic execution loop wrapped around a **dynamic graph database**.

It is **not**:
- a learning system
- an optimizer
- a planner
- an adaptive algorithm
- an AGI substrate

It is a **finite, inspectable state machine**.

### Allowed CORE Changes

Only the following are permitted:

- Bug fixes
- Performance optimizations
- Safety / determinism hardening
- FACET driver compatibility updates

Anything else is **forbidden**.

### Decision Rationale (ADR)

**Context:** Modern AI systems suffer from hallucination — generating plausible but false outputs.

**Decision:** Kremis separates Intelligence (CORTEX) from Truth (CORE). The CORE is closed and deterministic.

**Alternatives Considered:**
1. **Open plugin architecture** — Rejected: allows injection of non-deterministic logic
2. **Probabilistic graph weights** — Rejected: introduces floating-point non-reproducibility
3. **Embedded LLM in Core** — Rejected: violates grounding principle

**Consequences:**
- (+) All outputs are verifiable via graph traversal
- (+) Bit-exact reproducibility across runs
- (-) Limited expressiveness without CORTEX layer
- (-) Requires external intelligence for complex queries

---

## 2. What Kremis Is NOT (Binding Constraints)

> **Cross-Reference:** For the authoritative, binding version of these constraints,
> see [AGENTS.md Section 1](AGENTS.md#1-what-kremis-is-not-non-negotiable).

To prevent scope creep, hype, and conceptual drift, the following are **absolute constraints**:

| Concept | Status | Explanation |
|------|------|------------|
| **Unverified Generation** | **FORBIDDEN** | AGI cannot produce output without consulting the Graph |
| **Silent Hallucination** | **CRITICAL FAILURE** | If the Graph does not confirm, AGI must return "I don't know" |
| **Core Mutability** | **RESTRICTED** | The AI cannot rewrite base rules, only add data |
| **Stochasticity in Core** | **FORBIDDEN** | The Core remains deterministic and reproducible |
| **Anthropomorphism** | **FORBIDDEN** | No language implying consciousness or intentionality |

### Forbidden Statements

The following phrases are **incorrect by definition**:

- ❌ “Kremis learns”
- ❌ “Kremis understands”
- ❌ “Kremis becomes smarter”

Correct formulations:

- ✅ “Graph density increased”
- ✅ “New edges were crystallized”
- ✅ “Traversal depth expanded”

---

## 2.1 Three-Pillar Architecture (INGESTOR → GRAPH ENGINE → COMPOSITOR)

Kremis is **designed around** a three-pillar pipeline (historically inspired by biological cognition):

```text
  INGESTOR        GRAPH ENGINE     COMPOSITOR
    │               │               │
    ▼               ▼               ▼
┌────────┐    ┌──────────┐    ┌───────────┐
│   RX   │ ──▶│  STORE   │──▶ │    TX     │
│(Input) │    │ (Graph)  │    │ (Output)  │
└────────┘    └──────────┘    └───────────┘
```

### Unified Terminology Table

| Component | Rust Module | AGENTS.md | Description |
|-----------|-------------|-----------|-------------|
| **INGESTOR** | `RX` | INGESTOR | Perceive and normalize signals from world |
| **GRAPH ENGINE** | `STORE` | GRAPH ENGINE | Store, associate, and retrieve structure |
| **COMPOSITOR** | `TX` | COMPOSITOR | Assemble and emit artifacts to world |
| *(internal)* | `BUFFER` | Active Context | Session-local volatile working memory |

The original biological metaphors (SENSES/BRAIN/MOUTH) are **deprecated aliases** preserved only for conceptual origin.
The system uses strict technical terminology.

**Key Principle:** Signal flows INGESTOR → GRAPH ENGINE → COMPOSITOR. Never backwards, never skipped.

---

## 3. CORE vs FACETS (Hard Boundary)

Kremis enforces a **hard architectural separation**.

### 3.1 The CORE (Immutable Internal Logic)

The CORE is the **only component allowed to own state**.

**Responsibilities:**
- Signal ingestion (Validation)
- Graph CRUD operations
- Deterministic path traversal
- Validation and null-response enforcement

**Explicitly excluded from the CORE:**
- Planning
- Goal systems
- Optimization
- Self-modification
- Interpretation
- Semantics

**CORE Components:**

- **RX (Receiver)**
  Accepts normalized signals. No interpretation.

- **STORE (Graph DB)**
  The **only persistent memory** in the system.

- **TX (Transmitter)**
  Assembles output strictly from graph traversal results.

- **BUFFER**
  Volatile, session-scoped scratch space.

- **PRIMITIVES**
  Hardcoded Rust functions for segmentation, linking, and validation.
  Immutable at runtime.

---

### 3.2 FACETS (External Adapters)

FACETS are **epistemically stateless** peripherals.
They adapt external reality to the CORE interface and vice-versa.

> [!IMPORTANT]
> **GOLDEN RULE:** In case of error or malfunction of a Facet, the maximum permissible
> damage is a rejected input or null output. A Facet MUST NEVER be able to introduce
> a false truth into the Core.

#### 3.2.1 Technical State vs Epistemic State

| State Type | Definition | FACETS Policy |
|------------|------------|---------------|
| **Epistemic State** | Knowledge, beliefs, inferences, semantic relationships | ❌ PROHIBITED |
| **Technical State** | Caches, buffers, configs, sessions, retry counters | ✅ PERMITTED |

FACETS are "stateless" in the **epistemic** sense: they hold no beliefs, make no inferences,
and maintain no semantic memory. Technical state for operational efficiency is allowed.

#### 3.2.2 FACETS MAY (Permitted Operations)

- **Normalize inputs:** casing, trimming, encoding conversion, format parsing
- **Transform formats:** JSON ↔ Signal, HTTP ↔ raw bytes, file ↔ stream
- **Use configuration DSLs:** mapping rules (input field → entity type)
- **Maintain technical state:** connection pools, caches, session tokens, retry state
- **Orchestrate I/O:** batching, retry, backoff, connection management
- **Handle technical errors:** timeouts, network failures, format errors
- **Decide *how* to communicate:** protocol selection, encoding, transport

#### 3.2.3 FACETS MUST NOT (Absolute Prohibitions)

1. **Infer semantic relationships** between entities
2. **Invent or complete missing data** (no "guessing")
3. **Decide what is true** (no epistemic authority)
4. **Modify the STORE** without passing through CORE validation
5. **Filter signals based on content meaning** (only format-based rejection allowed)
6. **Produce output not validated by CORE**

**Examples:**
- `FileFacet` - File system read/write
- `JsonFacet` - JSON serialization/deserialization
- `TextFacet` - Plain text normalization
- `Transducer` - Configurable field→entity mapping

FACETS may be intelligent (e.g., use ML for format detection), but are **never authoritative**.
Their output must be validated by the Core before affecting the graph or reaching the user.

---

## 4. Forbidden Design Patterns

Any contribution introducing these patterns is **automatically rejected**:

| Pattern | Reason |
|------|------|
| Predictive Generation | Violates determinism |
| Pre-trained Models | Violates grounding |
| “Enhancer” Modules | Violates closed core |
| Shadow Logic | Violates transparency |
| Floating-Point Weights | Violates exactness |
| Implicit Defaults | Violates traceability |

Connections are **explicit or nonexistent**.
No probabilities, no guesses.

---

## 5. Deterministic Data Flow

Kremis operates on a **strict bidirectional I/O loop**:

```text
[ External Reality ]
       ▲  ▼
       │  │ (Raw Signals)
       ▼  ▲
┌─────────────────────┐
│      FACETS         │ (Transducers)
└─────────┬───────────┘
          │ (Normalized Protocol)
          ▼
┌─────────────────────┐
│ CORE (Rust)         │
│                     │
│  RX → STORE → TX    │
│          ▲          │
│          │          │
│       PRIMITIVES    │
└─────────────────────┘
```

**Invariant Rules:**
1. `RX` never communicates directly with `TX`.
2. All information **must** pass through `STORE`.
3. The CORE never initiates interaction; it only responds to ticks or signals.

---

## 6. Memory Architecture (Structural, Not Cognitive)

Memory in Kremis is **structural**, not semantic.

### Memory Layers (Reference Pattern – FACET Implementable)

> [!IMPORTANT]
> The following layered architecture is a **reference pattern**.
> The minimal CORE requires ONLY: nodes, edges, integer weights, and **Active Context (Buffer)**.
> Layer separation, promotion thresholds, and lifecycle policies
> are **FACET responsibilities**, not CORE requirements.

1. **Active Context (Volatile Buffer)**
   Session-local, currently activated nodes, cleared on reset.


2. **Provisional Layer (Virtual View)**
   Logical subset of edges where `weight < STABLE_THRESHOLD`. 
   **Not a separate buffer.** These edges exist in the STORE but are treated as "weak" by Facets.

3. **Stable Layer (Persistent Graph)**
   Logical subset of edges where `weight >= STABLE_THRESHOLD`.
   Crystallized, high-confidence structure.

### 6.1 Scalable Storage (Conceptual Model)

The minimal CORE must support graphs of arbitrary size, exceeding available RAM.

**Reference Implementation Strategy:**
- **Transactional Persistence:** Use of an embedded, ACID-compliant storage engine (e.g., B-Tree based) to guarantee data integrity without manual filesystem management.
- **Lazy Loading:** The Graph Engine fetches nodes/edges from disk only when requested by traversal.
- **Canonical Export:** While internal storage is optimized for speed, the system maintains the ability to export a "Bit-Exact" snapshot for cryptographic verification.


### Null Protocol (MANDATORY)

**Honesty is defined as the ability to return `None` when supporting structure is missing, rather than fabricating a path.**

If a traversal targets a missing node or edge:

```rust
return None;  // Option<T> - idiomatic Rust
```

Guessing, filling gaps, or fabricating paths is a **critical system fault**.

---

## 7. Validation Tiers (Engineering Metrics)

Kremis uses **engineering validation tiers**, not biological metaphors.

| Tier | Definition |
|----|-----------|
| **T0** | Signal integrity preserved |
| **T1** | Deterministic edge creation |
| **T2** | Single-hop traversal correctness |
| **T3** | Multi-hop traversal correctness |

If a tier fails, the system is **invalid**, not “immature”.

---

## 8. Innate Primitives (Hardcoded Runtime)

Kremis starts with **zero data** but **fixed logic**.

These primitives must be compiled into the binary:

1. **Segmentation Primitive**
   Splits input streams into discrete units.

2. **Linking Primitive**
   Creates directed edges between sequential units based on strictly adjacent temporal occurrence.
   **Constant:** `ASSOCIATION_WINDOW = 1`. (A connects to B only if B immediately follows A).

3. **Topology Validation Primitive**
   Checks graph continuity. If a required link is missing during traversal, it returns `None` (Null Protocol).

**Key Distinction:**

| Component | Mutability |
|--------|-----------|
| Rust Binaries | Immutable |
| Graph Data | Mutable via experience |

---

## 9. Developmental Stages (FACET – Capability Maturation)

> [!WARNING]
> **This section describes a FACET, not CORE functionality.**
> The CORE does NOT implement stages, capabilities, or maturation.
> Stage assessment and capability gating are external FACET responsibilities.

The following stages describe a **reference FACET implementation**
for gating capabilities based on graph metrics.

> [!NOTE]
> **GAP Resolution:** The edge counts below (100, 1000, 5000) are **illustrative placeholders** for order-of-magnitude logic.
> Real-world thresholds will likely be orders of magnitude higher (e.g., millions for S2).


### Stage Definitions

| Stage | Name | Capabilities | Graph Threshold |
|-------|------|--------------|-----------------|
| **S0** | **Signal Segmentation** | Basic signal segmentation, primitive linking | 0 nodes |
| **S1** | **Pattern Crystallization** | Grammar induction, simple pattern generation | ~100 stable edges |
| **S2** | **Causal Chaining** | Causality detection, temporal memory, causal chain extraction | ~1000 stable edges |
| **S3** | **Recursive Optimization** | Goal planning (external), external facet triggers, world modification | ~5000 stable edges |

### Stage Transitions

Transitions are triggered by **structural thresholds** only:
- Graph density (edge count / node count)
- Stable edge count
- Traversal depth capability

Transitions are **NOT** triggered by:
- Time elapsed
- External intervention
- Arbitrary decisions

### Stage Components

1. **Stage Assessor**
   Evaluates graph metrics to determine current stage readiness.
   Pure function: `assess(graph: &Graph) -> Stage`

2. **Stage Manager**
   Orchestrates transitions and unlocks stage-specific primitives.
   No state beyond current stage indicator.

### Constraint

Stage transitions are **irreversible and deterministic**.
A graph that meets S2 thresholds will always be classified as S2.

---

## 10. Extensibility Rules

Kremis is **extensible only through FACETS**.

Allowed:
- New I/O channels
- New environments
- New signal sources

Forbidden:
- CORE replacement
- CORE augmentation
- Hidden cognition layers
- “Advanced graph intelligence”

If you need more power, build it **outside** the CORE.

---

## 11. Source-of-Truth Documents

| File | Authority |
|----|----------|
| `AGENTS.md` | **Highest – Binding rules** |
| `KREMIS.md` | Architecture & philosophy |
| `ROADMAP.md` | Implementation tracking |

If a conflict exists, **AGENTS.md wins**.

---

## Final Statement

Kremis is **Honest Intelligence**.
It is a **neuro-symbolic architecture** designed to be:

- Inspectable
- Predictable
- Grounded
- Honest about ignorance
- Verifiable before output

Anything else is **out of scope by design**.

---

**License:** Apache License 2.0
**Last Updated:** 2026-01-20
**Version:** 0.1.0

