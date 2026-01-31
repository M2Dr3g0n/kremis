# Kremis CORTEX

The **Cortex** is the intelligent layer for Kremis - a demonstration of "Honest AGI"
that enforces epistemic honesty through mandatory topological verification.

## Overview

Cortex communicates with the Kremis Core via HTTP REST API, implementing the
**Honesty Protocol**:

1. Every inference MUST be validated by a Core query
2. `null` responses result in "UNKNOWN" status
3. All outputs use FACTS / INFERENCES / UNKNOWN template
4. Full audit logging of verification cycles

## Requirements

- Python 3.11+
- Running Kremis server (`kremis server`)

## Installation

```bash
cd cortex

# Using uv (recommended)
uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e .

# Using pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

### Start the Kremis Server First

```bash
# In one terminal
cargo run -p kremis -- server --port 8080
```

### Interactive REPL

```bash
kremis-cortex repl
```

### Single Query

```bash
kremis-cortex query "lookup 42"
kremis-cortex query "ingest 1 name Alice"
```

### Check Status

```bash
kremis-cortex status
```

### Custom Server URL

```bash
kremis-cortex --server http://localhost:9000 repl
```

## Commands

| Command | Description |
|---------|-------------|
| `lookup <entity_id>` | Look up an entity by ID |
| `traverse <node_id> [depth]` | Traverse graph from node |
| `path <start> <end>` | Find strongest path between nodes |
| `ingest <id> <attr> <value>` | Ingest a signal |
| `status` | Show graph statistics |
| `stage` | Show developmental stage |
| `audit` | Show verification audit summary |
| `help` | Show help |
| `quit` | Exit |

## Architecture

```
+---------------------------------------------+
|                   CORTEX                    |
|  +-----------+  +--------------+  +-------+ |
|  | User REPL |->| Hypothesis   |->|Honesty| |
|  |           |  | Generator    |  |Protocol |
|  +-----------+  +--------------+  +---+---+ |
+---------------------------------------+-----+
                                        | HTTP REST
+---------------------------------------+-----+
|                KREMIS CORE            v     |
|  +---------+  +-----------+  +-----------+ |
|  | axum    |->| Graph     |->| Grounding | |
|  | Server  |  | Engine    |  | Module    | |
|  +---------+  +-----------+  +-----------+ |
+---------------------------------------------+
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Connection check |
| `/status` | GET | Graph statistics |
| `/stage` | GET | Developmental stage |
| `/signal` | POST | Ingest signals |
| `/query` | POST | Execute queries |

## Query Types

```json
// Lookup entity
{"type": "lookup", "entity_id": 42}

// Traverse from node
{"type": "traverse", "node_id": 1, "depth": 3}

// Find strongest path
{"type": "strongest_path", "start": 1, "end": 5}

// Find intersection
{"type": "intersect", "nodes": [1, 2, 3]}

// Related subgraph
{"type": "related", "node_id": 1, "depth": 2}
```

## Honesty Protocol

The Cortex **NEVER** guesses or fills gaps. When the Core returns no supporting
structure:

- DO NOT guess or fill gaps
- DO NOT hallucinate connections
- DO say "I don't know"
- DO explain what's missing

This is what makes Kremis an "Honest AGI".

### Output Format

```
+-------------------------------------+
| FACTS (Extracted from Core)        |
| - [FACT] Statement [path: 1 -> 2]  |
+-------------------------------------+
| INFERENCES (CORTEX deductions)     |
| - [INFERENCE] Statement [85%]      |
+-------------------------------------+
| UNKNOWN (Core returned None)       |
| - [UNKNOWN] Query: Explanation     |
+-------------------------------------+
```

## Programmatic Usage

```python
from kremis_cortex import KremisClient, Cortex, HonestResponse

# Direct client usage
client = KremisClient(base_url="http://localhost:8080")
if client.start():
    # Ingest a signal
    node_id = client.ingest_signal(1, "name", "Alice")

    # Query
    result = client.lookup(1)
    if result and result.verified:
        print(f"Found! Path: {result.evidence_path}")

    # Get status
    status = client.get_status()
    print(f"Nodes: {status['node_count']}")

    client.stop()

# Using Cortex class
cortex = Cortex()
if cortex.start():
    response = cortex.query("lookup 1")
    print(response.to_text())
    cortex.stop()
```

## Async Client

```python
import asyncio
from kremis_cortex import AsyncKremisClient

async def main():
    client = AsyncKremisClient()
    if await client.start():
        result = await client.lookup(1)
        await client.stop()

asyncio.run(main())
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Type checking (if mypy installed)
mypy kremis_cortex
```

## License

Apache License 2.0
