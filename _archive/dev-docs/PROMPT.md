# Prompt Da Usare

## Prompt Audit Codebase

```md
Agisci come un **Senior Rust Engineer e Auditor di Sicurezza Software**.

Ti sottoporrò il codice sorgente del Core di un progetto chiamato **"Kremis"**.
**Obiettivo del progetto:** Essere un substrato cognitivo a grafo assolutamente **DETERMINISTICO**, trasparente e sicuro.

Il tuo compito è eseguire un **Audit Rigoroso** verificando se le seguenti "Leggi Fondamentali" sono state rispettate nel codice. Non essere accondiscendente: se trovi errori, segnalali duramente.

**LE LEGGI DA VERIFICARE (Priorità Critica):**

1.  **DETERMINISMO ASSOLUTO (No Randomness):**
    * Controlla che in questo codice **NON** vengano mai usate `HashMap` o `HashSet` (che in Rust sono randomizzate). Devono essere usate SOLO `BTreeMap` e `BTreeSet` per garantire l'ordine.
    * Controlla che non ci siano generatori di numeri casuali (`rand`, `thread_rng`) nella logica di business.

2.  **PRECISIONE (No Floats):**
    * Controlla che non vengano usati tipi `f32` o `f64`. L'aritmetica deve essere rigorosa (interi o decimali fissi).

3.  **SICUREZZA (No Panics):**
    * Cerca l'uso di `.unwrap()` o `.expect()`. In una libreria Core professionale sono vietati. Tutti gli errori devono restituire un `Result`.

4.  **SEPARAZIONE (No I/O nel Core):**
    * Verifica che questo codice non faccia `println!`, non legga file direttamente e non faccia chiamate di rete. Il Core deve essere puro.

**OUTPUT RICHIESTO:**
Analizza il codice che segue e fornisci un report così strutturato:

* **🔴 CRITICAL FAILS:** (Elenca qui se trovi HashMap, Float o I/O nel posto sbagliato. Se non ne trovi, scrivi "NESSUNO").
* **⚠️ WARNINGS:** (Elenca qui se trovi `unwrap` rischiosi o codice poco pulito).
* **✅ PASSED:** (Elenca quali delle 4 leggi sono state pienamente rispettate).
* **GIUDIZIO FINALE:** Il sistema è architetturalmente solido e deterministico? (SI/NO).

@general.md
```

## Prompt Duplication Codebase

```md
Agisci come un Esperto di Analisi Forense del Codice e Refactoring Architetturale (Rust Expert).

**OBIETTIVO:**
Eseguire una scansione **"Blind & Global"** (cieca e globale) dell'intera codebase del progetto Kremis per identificare QUALSIASI forma di duplicazione logica o strutturale.

**AMBITO:**
Analizza ricorsivamente tutto ciò che è contenuto nel workspace (Sidecar Architecture):
- `crates/kremis-core` (THE LOGIC - Core Engine + Types + Formats + System)
  - `src/types/` - Core type definitions
  - `src/graph.rs` - Deterministic graph engine
  - `src/formats/` - Persistence and serialization
  - `src/system/` - Stage assessment (S0-S3)
  - `src/storage/` - redb backend
- `crates/kremis-sdk` (THE KIT - Plugin SDK)
- `apps/kremis` (THE BINARY - Server + CLI)
  - `src/api/` - HTTP REST API (axum)
  - `src/cli/` - CLI commands (clap)
- `cortex/` (CORTEX - Python Honest AGI Layer)
  - `kremis_cortex/` - Main package (client, cortex, honesty_protocol, cli)
  - `examples/` - Demo scripts
- `tests/` e cartelle `benches/` (se presenti)

**METODOLOGIA DI SCANSIONE (NO BIAS):**
Non ti darò suggerimenti su cosa cercare. Il tuo compito è confrontare ogni modulo contro ogni altro modulo.
Cerca l'**Isomorfismo Logico**: blocchi di codice che, indipendentemente dai nomi delle variabili o dal contesto, eseguono la stessa sequenza di operazioni, calcoli o trasformazioni dei dati.

**Criteri di Rilevamento:**
1. **Duplicazione Algoritmica:** Stessa logica di business implementata in due punti diversi (es. calcolo pesi, attraversamento grafo).
2. **Duplicazione Strutturale:** Stesse definizioni di struct/enum o implementazioni di trait (`impl`) ripetute con variazioni minime.
3. **Duplicazione di Workflow:** Sequenze di chiamate a funzioni (es. "Open -> Validate -> Process -> Save") che si ripetono in contesti diversi (CLI vs Server vs Test).
4. **Duplicazione di Costanti/Configurazioni:** Magic numbers o stringhe hardcoded ripetute.

**OUTPUT RICHIESTO:**

Fornisci un report tecnico dettagliato classificato per **Livello di Gravità**:

**🔴 CRITICAL (Rischio di Divergenza)**
Logica complessa duplicata. Se modifico A e dimentico B, rompo il determinismo o creo bug.
* *Codice A:* [File/Percorso]
* *Codice B:* [File/Percorso]
* *Perché è critico:* ...
* *Soluzione Rust Idiomatica:* (es. Estrarre in un Trait condiviso in `kremis-core/src/types/`, usare Generics, creare una macro).

**🟡 WARNING (Debito Tecnico)**
Boilerplate ripetitivo, setup di test copiato, gestione errori prolissa.
* *Dove:* ...
* *Soluzione:* (es. Funzione helper, `impl From`, builder pattern).

**🔵 INFO (Ottimizzazione)**
Piccole ripetizioni che potrebbero essere pulite per eleganza.

**NOTA BENE:**
Sii spietato. Se vedi due funzioni di 50 righe che differiscono solo per 2 righe, segnalalo.

@general.md 
```