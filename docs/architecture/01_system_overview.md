# System overview

```text
[manifests + config]
        |
        v
[Snakemake orchestrator]
  - profiles: test / portable / accelerated
  - cache-first layout
        |
        v
[feature modules]
  - similarity (sourmash)
  - safety (abricate + lysogeny flags)
  - structural (foldseek summaries)
        |
        v
[Decision Bundle outputs]
  - rankings/<host_id>/ranking.csv
  - rankings/<host_id>/evidence_bundle.json
  - optional test_plan.md
```

Key idea: contracts first, modules swappable. The pipeline always produces the same output artifacts
(`ranking.csv`, `evidence_bundle.json`), while feature modules can be mocked or replaced by real implementations
without changing the contract.

What this repo demonstrates today:
- manifest-driven ID axis (`host_id`, `phage_id`)
- a reproducible Snakemake DAG
- deterministic mock modules
- a decision bundle output with provenance fields

What it is not (yet):
- a validated clinical decision system
- a full structural pipeline with cached folding and real Foldseek hits
