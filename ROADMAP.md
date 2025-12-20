# Roadmap

## v0.1 — Architecture stub (now)
- Manifest-driven IDs, config contract, profiles
- Deterministic mock modules
- Stable output contract (ranking + evidence bundle)
- Demo outputs committed for inspection

## v0.2 — Baseline MVP (portable)
- Replace mock similarity with real `sourmash` (cached sketches)
- Replace mock safety with real `abricate` (+ minimal lysogeny heuristic)
- Same output contract, richer evidence bundle

## v0.3 — Structural evidence (cached)
- Foldseek search using cached structures
- Evidence bundle includes structural summaries and explanations
- Host artefacts cached per host_id

## v0.4 — ColabFold caching + host on-demand
- Phage library folding cached (build once)
- Host folding on-demand, cached
- Runtime targets documented (e.g., 1 host × 100 phages within hours)

## v0.5 — Feedback loop / learning layer
- Ingest wet-lab results (hit/no-hit, EOP where available)
- Model training stub (baseline ranking -> learned ranking)
- Provenance and dataset versioning (DVC/MLflow-style)
