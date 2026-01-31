# Integrazioni Future

> Documento di brainstorming per funzionalità future di Kremis.
> Queste sono **idee**, non piani approvati.

---

## 1. Strategia di Mercato: "Unbeatable"

### 1.1 Soluzione al "Cold Start" - Marketplace of Truth

**Problema:** Kremis parte vuoto. L'utente deve ingerire milioni di segnali prima che sia utile.

**Soluzione:** Creare pacchetti `.krex` pre-costruiti e verificati:
- "Kremis-Wikipedia-Lite"
- "Kremis-Civil-Code-IT"
- "Kremis-Medical-PubMed"

**Vantaggio:** L'utente scarica Kremis + pacchetto "Legge Italiana". In 30 secondi ha un'AI che non può mentire sulle leggi.

### 1.2 Soluzione alla "Stupidità" - One-Line Brain Implant

**Problema:** Il Core non pensa, convalida solo.

**Soluzione:** Middleware universale che intercetta chiamate OpenAI/Anthropic:
```python
kremis.wrap(openai_client)
```

**Implementazione conforme all'Honesty Protocol (AGENTS.md 2.4):**

Il middleware NON "migliora" le risposte LLM (violerebbe F1). Può solo:
- ✅ **ACCEPT** → Path trovato nel grafo → Etichetta come `[FACT]`
- ✅ **PARTIAL** → Path parziale (confidence < 70%) → Etichetta come `[INFERENCE]`
- ✅ **REJECT** → Nessun path di supporto → Etichetta come `[UNVERIFIED]` o sopprimi

```python
# Esempio di output middleware
response = kremis.wrap(openai_client).chat("Chi è Alice?")
# Output:
# [FACT] Alice esiste nel sistema [path: 1]
# [INFERENCE] Alice potrebbe conoscere Bob [confidence: 65%]
# [UNVERIFIED] Alice lavora in Google (nessun supporto nel grafo)
```

**Vincolo critico:** Le claim `[UNVERIFIED]` devono essere chiaramente marcate, MAI passate silenziosamente come fatti.

### 1.3 Soluzione alla Scalabilità - Fractal Scaling

**Problema:** Core single-threaded, DB embedded.

**Soluzione:** I Facet sono stateless → possono essere distribuiti su Edge (Cloudflare Workers) mentre il Core resta isolato.

---

## 2. Miglioramenti Tecnici

### 2.1 Consenso per Ripetizione

Sfruttare `EdgeWeight` per validare dati:
```
const STABLE_THRESHOLD: i64 = 3;
```
- Query corretta: "Dammi i vicini di X dove `weight >= 3`"
- Un dato diventa "verità" solo dopo 3 conferme indipendenti

### 2.2 Dictionary Import Facet (ex "Synonym Facet")

**Problema:** Per il Core "Auto" e "Macchina" sono estranei.

**Soluzione:** Facet **Transducer** che importa dizionari espliciti pre-esistenti.

**Implementazione conforme (AGENTS.md 2.2 - Facet NON inferisce relazioni semantiche):**

```
Fonte: Dizionario esplicito (es. Wiktionary dump, WordNet)
       ↓
Transducer: Trasformazione rule-based (NO NLP inferenziale)
       ↓
Signal: (Auto) -> [sinonimo:wiktionary] -> (Macchina)
```

**Vincoli:**
- ❌ **VIETATO:** Usare NLP/LLM per "scoprire" sinonimi (viola F3: Heuristic Filling)
- ❌ **VIETATO:** Inferire relazioni semantiche nel Facet
- ✅ **PERMESSO:** Trasformare dizionari strutturati in Signals
- ✅ **PERMESSO:** Includere provenienza nell'attributo (`sinonimo:wiktionary`)

**Esempio di Transducer conforme:**
```python
# Input: riga da dump Wiktionary
# "auto|macchina|vettura|automobile"

def wiktionary_to_signals(line: str) -> list[Signal]:
    words = line.split("|")
    base = words[0]
    return [
        Signal(entity_id=hash(base),
               attribute=f"sinonimo:wiktionary",
               value=synonym)
        for synonym in words[1:]
    ]
```

**Nota:** Il Facet è un puro trasformatore di formato, non un sistema intelligente.

### 2.3 Diagnostic Side-Channel

**Problema:** `None` è pedagogicamente inutile per CORTEX.

**Soluzione:** Codici di errore strutturati:
```rust
EdgeMissing(A, B)
NodeNotFound(X)
PathTooLong(start, end, max_depth)
```

### 2.4 Tiered Caching Strategy

**Problema:** Traversate complesse diventano lente con grafi grandi.

**Soluzione:** Cache a tre livelli con **garanzia di trasparenza**.

**Architettura:**
1. **Hot Tier (RAM):** Ultimi 10.000 nodi
2. **Warm Tier (OS Cache):** Pagine redb cached
3. **Cold Tier (Disk):** Nodi storici

**Vincoli di determinismo (AGENTS.md 5.3):**

La cache è **strettamente un'ottimizzazione di performance**. DEVE garantire:
- ✅ **Trasparenza:** Stesso input = stesso output (indipendentemente dallo stato cache)
- ✅ **Invalidazione:** Cache invalidata su `export_canonical()` per garantire stato canonico
- ✅ **Logical Clock:** Usare clock monotono (NON wall-clock) per eviction (già in `cache.rs`)
- ❌ **VIETATO:** Usare cache hit/miss per alterare risultati query

**Implementazione conforme:**
```rust
// La cache usa BTreeMap (NON HashMap) per ordinamento deterministico
// L'eviction usa logical_clock: u64 (NON timestamp)
pub struct LruCache<K: Ord + Clone, V: Clone> {
    entries: BTreeMap<K, CacheEntry<V>>,
    logical_clock: u64,  // Monotonic, NOT wall-clock
    // ...
}
```

**Nota:** Il Core attuale (`cache.rs`) già implementa questi vincoli correttamente.

### 2.5 Merkle Tree State Hashing

**Problema:** File redb non bit-identical.

**Soluzione:** Hash progressivo del grafo (Merkle Root) incluso in export canonico.

---

## 3. Architettura AGI-Kremis

### 3.1 Il Loop "Sognatore & Giudice"

```
CORTEX (Python/LLM) ←→ CORE (Rust/Kremis)
     Sognatore              Giudice
     Creativo               Onesto
     Bugiardo               Deterministico
```

L'AGI nasce dal conflitto tra i due.

### 3.2 Reality Check Loop

1. **Input:** Utente chiede qualcosa
2. **Ipotesi:** CORTEX genera risposte con LLM
3. **Query:** CORTEX traduce in query Kremis
4. **Verifica:** Core conferma o nega
5. **Output:** Risposta etichettata FACTS / INFERENCES / UNKNOWN

### 3.3 Epistemic Foraging (Apprendimento Attivo)

Quando Kremis restituisce `None`:
1. CORTEX attiva Facet di ricerca
2. Legge documenti esterni
3. Normalizza in Signals
4. Ingesta nel Core
5. Riprova la query

**Vincoli di conformità (AGENTS.md 2.2, 2.3):**

CORTEX agisce come **orchestratore**, NON come **decisore semantico**:

```
┌─────────────────────────────────────────────────────────────┐
│  CORTEX (Orchestratore)                                     │
│  ├── Decisione TECNICA: quale fonte consultare              │
│  ├── NON decide COSA sia vero                               │
│  └── NON genera Signals con LLM                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  FACET Transducer (Rule-based)                              │
│  ├── Estrae Signals da documenti strutturati                │
│  ├── Trasformazione deterministica                          │
│  └── Include provenienza: attribute="fatto:wikipedia"       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CORE (Validatore)                                          │
│  ├── Ingesta Signals                                        │
│  └── Query retry                                            │
└─────────────────────────────────────────────────────────────┘
```

**Vincoli:**
- ❌ **VIETATO:** CORTEX genera Signals basati su inferenza LLM (viola F3)
- ❌ **VIETATO:** Facet "interpreta" documenti (deve solo trasformare formato)
- ✅ **PERMESSO:** CORTEX seleziona fonti (decisione tecnica, non epistemica)
- ✅ **PERMESSO:** Facet estrae dati strutturati con regole deterministiche
- ✅ **OBBLIGATORIO:** Tutti i Signals devono essere tracciabili a documento sorgente

### 3.4 Ragionamento Transitivo (Query-Time, Non Materializzato)

> ⚠️ **NOTA:** La proposta originale "Consolidamento Notturno" (creare archi transitivi nel Core)
> è stata **rimossa** perché viola F3 (Heuristic Filling) e il principio di grounding.

**Problema originale:** Come supportare ragionamento transitivo (A→B, B→C → A→C)?

**Soluzione conforme:** Inferenza transitiva calcolata **a query-time in CORTEX**, MAI materializzata nel Core.

```
┌─────────────────────────────────────────────────────────────┐
│  APPROCCIO CONFORME                                         │
├─────────────────────────────────────────────────────────────┤
│  1. CORTEX riceve query: "A è connesso a C?"                │
│  2. Core restituisce: path [A→B→C] (se esiste)              │
│  3. CORTEX calcola: "A→C derivabile da A→B→C"               │
│  4. Output etichettato: [INFERENCE] A→C [derivato: A→B→C]   │
│  5. NESSUN arco scritto nel Graph                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  APPROCCIO VIETATO (viola F3, grounding)                    │
├─────────────────────────────────────────────────────────────┤
│  ❌ Durante idle, crea arco A→C con peso basso              │
│  ❌ "Consolida" inferenze nel grafo                         │
│  ❌ Qualsiasi mutazione senza Signal esterno                │
└─────────────────────────────────────────────────────────────┘
```

**Implementazione in CORTEX:**
```python
def transitive_query(start: int, end: int) -> HonestResponse:
    # 1. Query Core per path diretto
    direct = client.strongest_path(start, end)

    if direct and len(direct.path) == 2:
        # Path diretto: A→C
        return HonestResponse(facts=[
            Fact(f"{start}→{end} (diretto)", direct.evidence_path)
        ])
    elif direct and len(direct.path) > 2:
        # Path transitivo: A→B→...→C
        return HonestResponse(inferences=[
            Inference(
                f"{start}→{end} (transitivo)",
                confidence=compute_transitive_confidence(direct),
                reasoning=f"Derivato da path: {direct.path}"
            )
        ])
    else:
        # Nessun path
        return HonestResponse(unknowns=[
            Unknown(f"{start}→{end}", "Nessun path nel grafo")
        ])
```

**Vincoli:**
- ✅ **PERMESSO:** Calcolare inferenze transitive a query-time
- ✅ **PERMESSO:** Etichettare output come `[INFERENCE]` con reasoning
- ✅ **PERMESSO:** Utente richiede "Solo FACTS" vs "FACTS + INFERENCES"
- ❌ **VIETATO:** Scrivere archi inferiti nel Graph (viola F3)
- ❌ **VIETATO:** Mutazioni del grafo senza Signal esterno (viola grounding)
- ❌ **VIETATO:** Processi "idle" che modificano il Core

**Principio:** Il Core contiene SOLO struttura derivata da segnali esterni grounded.
Le inferenze sono computate on-demand da CORTEX e mai persistite.

---

## 4. Problemi Aperti (Da Risolvere)

| Problema | Stato | Note |
|----------|-------|------|
| Semantica errori Facet | ⚠️ Parziale | Diagnostic Side-Channel proposto |
| Regola promozione edge | ⚠️ Parziale | STABLE_THRESHOLD definito |
| Circuit breaker CORTEX | ❌ Aperto | Serve isolamento e backpressure |
| Invalidazione dati errati | ❌ Aperto | Come gestire correzioni? |
| Observability formale | ❌ Aperto | Serve logging strutturato |

---

## 5. Posizionamento Strategico

**Non competere sull'intelligenza. Competi sulla responsabilità.**

Anche se GPT-5 risolve le allucinazioni, è una "scatola nera". Kremis fornisce:
- Tracciabilità completa
- Verificabilità crittografica
- Compliance per Enterprise

**Use case principale:** Compliance Officer per contratti/normative.

---

## 6. Checklist di Conformità Architetturale

> Ogni proposta futura DEVE essere verificata contro questa checklist prima dell'approvazione.

### Pattern Vietati (F1-F5)

| ID | Pattern | Descrizione | Verifica |
|----|---------|-------------|----------|
| F1 | Smart Wrappers | Facet che "migliora" output del Core | ❌ VIETATO |
| F2 | Hidden State | Memoria epistemica fuori dal Graph Engine | ❌ VIETATO |
| F3 | Heuristic Filling | Inventare/indovinare informazioni mancanti | ❌ VIETATO |
| F4 | Goal Injection | Iniettare direttive/obiettivi nel Core | ❌ VIETATO |
| F5 | Unconstrained LLM | Output LLM senza validazione Core | ❌ VIETATO |

### Vincoli di Determinismo

| Vincolo | Descrizione | Verifica |
|---------|-------------|----------|
| BTreeMap Only | NO HashMap/HashSet nel Core | ✅ OBBLIGATORIO |
| Integer Arithmetic | NO float, NO f32/f64 | ✅ OBBLIGATORIO |
| No Randomness | NO rand, uuid, wall-clock | ✅ OBBLIGATORIO |
| Saturating Ops | Overflow → saturazione, MAI panic | ✅ OBBLIGATORIO |
| Bit-Exact Export | `export_canonical()` produce output identico | ✅ OBBLIGATORIO |

### Boundary Core/Facet

| Componente | Responsabilità | Stato |
|------------|----------------|-------|
| CORE | Ingestion, Storage, Retrieval | Stateful, Closed, Minimal |
| FACET | Transform I/O, NO semantic inference | Stateless (epistemically) |
| CORTEX | Orchestrate, Label, Query-time inference | NO write access to Graph |

### Honesty Protocol

| Requisito | Descrizione |
|-----------|-------------|
| FACTS | Solo se path esiste nel grafo |
| INFERENCES | Etichettate con confidence + reasoning |
| UNKNOWN | Core restituisce None → "Non lo so" |
| NO Hallucination | Mai inventare, mai indovinare |

### Template Valutazione Proposta

```markdown
## Proposta: [Nome]

### Conformità F1-F5
- [ ] F1: Non migliora output Core
- [ ] F2: Nessuno stato epistemico nascosto
- [ ] F3: Non inventa informazioni
- [ ] F4: Nessuna goal injection
- [ ] F5: LLM validato da Core

### Determinismo
- [ ] Usa BTreeMap (no HashMap)
- [ ] Aritmetica intera only
- [ ] Nessuna randomness

### Boundary
- [ ] Mutazioni solo via Signal
- [ ] Facet epistemically stateless
- [ ] CORTEX no write to Graph

### Honesty
- [ ] Output etichettato (FACT/INFERENCE/UNKNOWN)
- [ ] None → "Non lo so"
```

---

**Last Updated:** 2026-01-21
