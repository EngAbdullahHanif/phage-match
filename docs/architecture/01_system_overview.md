# System overview

```text
                   ┌──────────────────────────────┐
                   │        PhageMatch v0.1        │
                   │  (architecture / mock stub)   │
                   └──────────────┬───────────────┘
                                  │
                     manifests + config (contracts)
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │ Snakemake Orchestrator (DAG)  │
                   │  - profiles: test/portable/acc│
                   │  - cache-first layout         │
                   └───────┬─────────┬────────────┘
                           │         │
                           │         │
                 similarity│   safety│    structural PPI
                   (mock→) │   (mock→)│     (mock→)
                   sourmash│  abricate│  foldseek (+cached folding)
                           │         │
                           └─────┬───┘
                                 ▼
                   ┌──────────────────────────────┐
                   │   Decision Bundle Outputs     │
                   │  ranking.csv + evidence.json  │
                   │  + optional test_plan.md      │
                   └──────────────────────────────┘
```
Key idea: **contracts first, modules swappable**. The pipeline always produces the same output artifacts
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
