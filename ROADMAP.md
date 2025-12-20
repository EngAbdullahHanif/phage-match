# Roadmap

This roadmap is intentionally contract-first: downstream consumers rely on the Decision Bundle outputs, while feature modules evolve behind stable schemas.

## v0.1 - Baseline MVP (contracts + runnable triage)
- Manifest-driven IDs (`host_id`, `phage_id`) as the only primary axis
- Snakemake DAG as the single source of truth (legacy runner deprecated)
- Decision Bundle contract:
  - `rankings/<host_id>/ranking.csv`
  - `rankings/<host_id>/evidence_bundle.json`
- v0.1 feature set (real or mocked depending on profile/tooling):
  - sequence similarity: `sourmash` containment (cached sketches)
  - safety: `abricate` VFDB/toxin screening + conservative lysogeny flags
  - structural evidence: Foldseek hit summaries (designed for cached structures)
- Static viewer to inspect evidence bundles

## v0.2 - Cache hardening + metadata
- Formalize cache keys + `meta.json` for cached artefacts (input hashes + tool/db versions + params)
- Add automatic Decision Bundle validation (JSON schema + CSV column checks)
- Expand evidence bundle explanations (per-feature why)

## v0.3 - Structural evidence, production-ready
- Phage structure caching: build once per library phage
- Host structure on-demand + optional caching per host
- Foldseek DB indexing and fast re-runs (hours not weeks target)

## v0.4 - Feedback loop (learning layer)
- Ingest wet-lab outcomes (hit/no-hit, EOP where available)
- Baseline re-ranking with explicit dataset versioning
- Experiment tracking / evaluation harness (ablation + benchmark reports)

## v0.5 - Integrations (optional)
- LIMS/Lab notebook export hooks
- Phage bank catalogue integration
- Partner-facing dashboards
