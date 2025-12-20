# PhageMatch: a decision-bundle pipeline for phage shortlist triage (v0.1)

## Abstract
Phage therapy screening is often constrained by the cost and time of testing large phage libraries against a specific bacterial isolate.
PhageMatch is a decision-support workflow that prioritizes a short list of candidate phages to test first, while emitting an
audit-ready evidence bundle suitable for regulated or collaborative settings.
v0.1 is intentionally minimal: it combines (i) fast sequence sketch similarity, (ii) cached structural search summaries, and
(iii) conservative safety / temperateness flags.

## Core idea: a locked Decision Bundle contract
The pipeline is designed as a two-layer system:

- Layer A (this folder): academic narrative, evaluation, reproducibility.
- Layer B (repo root): productized workflow (Snakemake DAG, viewer, demo outputs).

Both layers share the same core output contract:
`contracts/decision_bundle/`.

## Methods (v0.1)

### Inputs (manifest-driven)
The workflow operates on two primary identifiers:

- `host_id` - one host isolate genome/proteome
- `phage_id` - one phage genome in a curated library

Manifests are the only required entrypoints:

- `manifests/hosts.tsv` (`host_id`, `genome_fna`, `proteome_faa`)
- `manifests/phages.tsv` (`phage_id`, `fasta`)

### Feature modules
v0.1 computes three evidence types and stores them as per-(host,phage) feature artefacts.

1) Sequence similarity baseline (sourmash)
We sketch genomes and compute containment similarity to provide a fast baseline signal.
This is not a host-range predictor by itself; it is a prioritization feature.

2) Structural PPI evidence (Foldseek summaries)
Phage structures are cached per library member; host structures are computed (or cached) per run.
Each run performs search + parsing rather than folding the entire phage bank.
Foldseek hits are summarized into lightweight evidence: hit counts, best e-value/score, and coverage proxies.

3) Safety and temperateness flags (abricate + conservative lysogeny heuristics)
We run VFDB/toxin/virulence screening and simple lysogeny marker detection (e.g., integrase-like proteins).
The safety module is conservative: it prefers "flag for review" over "declare safe".

### Ranking heuristic (v0.1)
Without labeled host-range data, v0.1 uses a transparent heuristic:

- start from similarity and/or structural support scores (0..1)
- apply safety penalties (do not hide candidates; flag them)
- output a ranked list + embedded evidence for each shortlisted candidate

The ranking logic is deliberately simple to keep it auditable and to enable meaningful ablation studies.

## Limitations
- v0.1 does not claim clinical efficacy.
- A high score does not guarantee lysis; wet-lab validation is required.
- Structural evidence depends on structure availability/quality; the pipeline records tool/db versions for comparability.

## References
See `references.bib` for citations.
