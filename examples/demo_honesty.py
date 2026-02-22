#!/usr/bin/env python3
"""
Kremis Honesty Demo
===================
Shows how Kremis validates LLM claims against a deterministic graph.
No pip install required. Standard library only. Python 3.9+.

Usage:
  # 1. Start the Kremis server (in a separate terminal):
  #      cargo run -p kremis -- init
  #      cargo run -p kremis -- server
  #
  # 2. Run this demo:
  python examples/demo_honesty.py            # mock LLM (no external deps)
  python examples/demo_honesty.py --ollama   # real Ollama LLM (qwen3:4b)
  python examples/demo_honesty.py --url http://localhost:8080
"""
from __future__ import annotations

import json
import sys
import argparse
import urllib.request
import urllib.error

# Force UTF-8 on Windows (default console is cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── ANSI colors ────────────────────────────────────────────────────────────────
BOLD  = "\033[1m"
GREEN = "\033[92m"
RED   = "\033[91m"
DIM   = "\033[2m"
RESET = "\033[0m"

BASE_URL = "http://localhost:8080"

# ── HTTP helpers ───────────────────────────────────────────────────────────────

def api(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    except Exception as e:
        sys.exit(
            f"\n{RED}Cannot connect to Kremis at {BASE_URL}{RESET}\n"
            f"{DIM}Start the server first:\n"
            f"  cargo run -p kremis -- init\n"
            f"  cargo run -p kremis -- server{RESET}\n"
            f"\nError: {e}\n"
        )

# ── Knowledge base ─────────────────────────────────────────────────────────────

# Same 9 signals as examples/sample_signals.json, plus Rust language tag.
SIGNALS: list[tuple[int, str, str]] = [
    (1, "name",     "Alice"),
    (1, "role",     "engineer"),
    (1, "works_on", "Kremis"),
    (1, "knows",    "Bob"),
    (2, "name",     "Bob"),
    (2, "role",     "designer"),
    (2, "works_on", "Kremis"),
    (3, "name",     "Kremis"),
    (3, "type",     "project"),
    (3, "language", "Rust"),
]

def setup_knowledge_base() -> None:
    print(f"\n{BOLD}Step 1 — Ingest knowledge base{RESET}")
    print(f"{DIM}(entity–attribute–value triples → deterministic graph){RESET}\n")
    for entity_id, attr, val in SIGNALS:
        r = api("POST", "/signal", {"entity_id": entity_id, "attribute": attr, "value": val})
        mark = f"{GREEN}✓{RESET}" if r.get("success") else f"{RED}✗ {r.get('error', '?')}{RESET}"
        print(f"  {mark}  [{entity_id}] {attr:10} = {val}")
    print()

# ── Kremis query helpers ───────────────────────────────────────────────────────

def get_alice_facts() -> tuple[list[dict], str]:
    """
    Returns Alice's properties from Kremis and the grounding label.
    Two queries: lookup (entity_id → node_id) then properties (node_id → values).
    """
    r = api("POST", "/query", {"type": "lookup", "entity_id": 1})
    if not r.get("found"):
        sys.exit(f"{RED}Alice not found in graph after ingest.{RESET}")
    node_id = r["path"][0]

    p = api("POST", "/query", {"type": "properties", "node_id": node_id})
    return p.get("properties", []), p.get("grounding", "unknown")

# ── Mock LLM ──────────────────────────────────────────────────────────────────

# Scripted response: confident, plausible, mixes facts with fabrications.
MOCK_LLM_CLAIMS = [
    "Alice is an engineer.",
    "Alice works on the Kremis project.",
    "Alice knows Bob.",
    "Alice holds a PhD in machine learning from MIT.",
    "Alice previously worked at DeepMind as a research lead.",
    "Alice manages a cross-functional team of 8 people.",
]

# ── Ollama LLM ────────────────────────────────────────────────────────────────

def ollama_claims(model: str = "qwen3:4b") -> list[str]:
    """Ask Ollama to invent facts about Alice. Returns one claim per line."""
    prompt = (
        "Make up 6 specific, confident facts about a person named Alice. "
        "Write one fact per line. No numbering. Be detailed and specific."
    )
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = json.loads(r.read()).get("response", "")
        return [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    except Exception as e:
        sys.exit(
            f"\n{RED}Ollama error: {e}{RESET}\n"
            f"{DIM}Is Ollama running?  →  ollama serve{RESET}\n"
        )

# ── Validator ─────────────────────────────────────────────────────────────────

def validate(claim: str, properties: list[dict]) -> tuple[str, str]:
    """
    Checks whether any non-name value Kremis knows appears in the claim text.
    Returns (grounding, matched_value_or_empty).

    Skips the "name" attribute: the entity's name appears in every claim
    mentioning it, which would make every claim look like a fact.
    We validate against actual facts: role, works_on, knows, etc.
    """
    claim_lower = claim.lower()
    for prop in properties:
        if prop["attribute"] == "name":
            continue  # name identifies the entity, not a fact to validate
        v = prop["value"].lower()
        if v in claim_lower:
            return "fact", prop["value"]
    return "unknown", ""

def print_verdict(claim: str, grounding: str, matched: str) -> None:
    if grounding == "fact":
        label = f"{GREEN}[FACT]{RESET}         "
        note  = f"{DIM}← Kremis: \"{matched}\"{RESET}"
    else:
        label = f"{RED}[NOT IN GRAPH]{RESET} "
        note  = f"{DIM}← Kremis: None{RESET}"
    print(f"  {label} {claim}")
    print(f"  {'':14}  {note}")

# ── Demo ──────────────────────────────────────────────────────────────────────

def run(use_ollama: bool) -> None:
    h = api("GET", "/health")
    print(f"\n{BOLD}Kremis Honesty Demo{RESET}  —  server v{h.get('version', '?')}")
    print("=" * 60)

    setup_knowledge_base()

    # Get what Kremis knows about Alice
    alice_props, grounding = get_alice_facts()
    known_values = {p["value"] for p in alice_props}

    # LLM step
    llm_mode = "Ollama (qwen3:4b)" if use_ollama else "Mock LLM — scripted response"
    print(f"{BOLD}Step 2 — LLM: \"Tell me about Alice\"{RESET}")
    print(f"{DIM}Mode: {llm_mode}{RESET}\n")

    claims = ollama_claims() if use_ollama else MOCK_LLM_CLAIMS
    for c in claims:
        print(f"  {DIM}›{RESET} {c}")
    print()

    # Kremis validation step
    print(f"{BOLD}Step 3 — Kremis validates each claim{RESET}")
    print(f"{DIM}(confirms only what was explicitly ingested){RESET}\n")
    print(f"  {DIM}Kremis knows about Alice: {known_values}{RESET}")
    print(f"  {DIM}Kremis grounding label:   \"{grounding}\"{RESET}")
    print()

    confirmed = 0
    for claim in claims:
        g, matched = validate(claim, alice_props)
        print_verdict(claim, g, matched)
        print()
        if g == "fact":
            confirmed += 1

    total = len(claims)
    not_found = total - confirmed

    print("-" * 60)
    print(f"  {BOLD}Confirmed by graph:{RESET}  {confirmed}/{total}")
    print(f"  {BOLD}Not in graph:      {RESET}  {not_found}/{total}  (hallucinations or unknown facts)")
    print()
    print(f"  {GREEN}■{RESET} [FACT]          path exists in Kremis  (grounding: fact)")
    print(f"  {RED}■{RESET} [NOT IN GRAPH]  Kremis returns None     (never fabricates)")
    print()
    print(f"  {DIM}The graph cannot hallucinate. It only confirms what was ingested.{RESET}")
    print()

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    global BASE_URL
    p = argparse.ArgumentParser(
        description="Kremis Honesty Demo — validates LLM claims against a deterministic graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python examples/demo_honesty.py              # mock LLM\n"
            "  python examples/demo_honesty.py --ollama     # real Ollama LLM\n"
            "  python examples/demo_honesty.py --url http://localhost:8080\n"
        ),
    )
    p.add_argument("--ollama", action="store_true", help="Use Ollama (qwen3:4b) instead of mock LLM")
    p.add_argument("--url", default="http://localhost:8080", help="Kremis server URL")
    args = p.parse_args()
    BASE_URL = args.url
    run(use_ollama=args.ollama)

if __name__ == "__main__":
    main()
