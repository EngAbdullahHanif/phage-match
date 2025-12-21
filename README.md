# PhageMatch (v0.1) two-layer repo with a locked Decision Bundle contract

PhageMatch is a **decision-support workflow**: given a host isolate and a phage library, it produces:

- a **ranked shortlist** of phages to test first (`ranking.csv`)
- an **audit-friendly evidence bundle** for explainability + provenance (`evidence_bundle.json`)
- an optional lightweight viewer (`viewer/`) that renders the bundle locally

The core design is a two-layer repo that shares one contract:

- **Layer A - Academic artefact:** `academic/` (methods, evaluation plan, reproducibility, citations)
- **Layer B - Product workflow:** Snakemake DAG + CLI scripts + viewer + demo outputs

Both layers share the same core contract in `contracts/decision_bundle/`.

## Quick start

Prereqs: `snakemake>=7` (ideally via conda) and Python 3.10+.

Run the deterministic demo (test profile / mocked modules):
```bash
snakemake -s Snakefile --configfile config.yaml --cores 1
```

Note: If `conda` is not on PATH, the workflow skips conda envs automatically; this is fine for mocked runs. Use `--use-conda` only when you want real tools.

Outputs (per host run):
```
rankings/<host_id>/ranking.csv
rankings/<host_id>/evidence_bundle.json
rankings/<host_id>/test_plan.md
```

Inspect without running:
- `demo_outputs/H001/ranking.csv`
- `demo_outputs/H001/evidence_bundle.json`
- `demo_outputs/H001/test_plan.md`

Viewer (zero-build, static):
- Run: `powershell -ExecutionPolicy Bypass -File .\run_demo.ps1`
- This runs the pipeline (unless `-DemoOnly`), starts a tiny local server, and opens the viewer. Requires `python` on PATH.

Demo launcher shortcuts (PowerShell):
```powershell
.\run_demo.ps1 -DemoOnly
.\run_demo.ps1 -Reset
```

## v0.1 scope

v0.1 produces a usable ranking without labeled host-range data by combining three transparent evidence types:

Must-have modules (real or mocked depending on profile/tooling):
- **Structural PPI evidence:** Foldseek hit summaries (counts, best e-value/score, coverage proxies)
- **Sequence similarity baseline:** `sourmash` containment similarity
- **Safety layer:** `abricate` (VFDB/toxin/virulence screening) + conservative lysogeny flags

Explicitly out of scope for v0.1:
- DNA2Vec / k-mer embedding ML pipeline
- TensorFlow/autoencoders / GNNs
- LIMS integration
- perfect lifestyle prediction

## Repo layout

- `Snakefile` -> delegates to `workflow/pm_v0_1/Snakefile`
- `config.yaml` + `profiles/` -> module toggles and parameters
- `manifests/` -> input contracts (`host_id`, `phage_id`)
- `contracts/decision_bundle/` -> the shared output contract
- `workflow/` + `scripts/` -> runnable pipeline (Snakemake is the source of truth)
- `rankings/` -> per-run outputs (gitignored)
- `cache/` -> cached artefacts (gitignored)
- `viewer/` -> static UI-like bundle viewer
- `academic/` -> paper-style narrative + evaluation/reproducibility
- `demo_outputs/` -> committed example bundle for H001

## The Decision Bundle contract (core)

**`ranking.csv`** (spreadsheet-friendly)
```csv
host_id,phage_id,rank,confidence_score,primary_reason,safety_flags
H001,P001,1,0.92,structural_support,none
H001,P002,2,0.61,sequence_similarity,possible_temperate
```

**`evidence_bundle.json`** (UI + audit)
- Schema: `contracts/decision_bundle/evidence_bundle.schema.json`
- Contains module statuses, params/versions snapshots, and a `shortlist` array with embedded evidence.

## Data policy (demo vs real)

- The repo **includes tiny mock inputs** in `data/` and `manifests/*.tsv` so GitHub users can run the demo end-to-end.
- **Real datasets should stay local** (not committed). Point the manifests to local paths; absolute or relative paths both work.
- Templates already exist: `manifests/hosts.tsv`, `manifests/phages.tsv`, and the larger examples `manifests/hosts_real.tsv`, `manifests/phages_real.tsv`.

## Running with real data

1) Populate manifests:
- `manifests/phages.tsv` (`phage_id`, `fasta`)
- `manifests/hosts.tsv` (`host_id`, `genome_fna`, `proteome_faa`)

2) Choose a profile:
- `profiles/test.yaml` - fully mocked (fast demo)
- `profiles/portable.yaml` - sourmash only (no GPU / no structures)
- `profiles/accelerated.yaml` - sourmash + safety + structural (requires tool installs and cached structures)

3) Run, e.g. portable:
```bash
snakemake -s Snakefile --configfile config.yaml --configfile profiles/portable.yaml --cores 4 --use-conda
```

Helper target:
```bash
snakemake -s Snakefile --configfile config.yaml --cores 1 validate
```

## Notes
- Snakemake is the orchestrator and single source of truth. `legacy/pipeline_main.py` is deprecated.
- Cache-first compute model: phage library artefacts are cached once; hosts are processed on-demand.
- PHASTER is not a primary axis (kept as optional legacy enrichment).

## Not medical advice
This is a software prototype. Wet-lab validation and clinical governance remain the source of truth.
