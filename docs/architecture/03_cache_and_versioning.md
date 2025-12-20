# Cache and versioning

## Cache-first principle
- **Phage library artefacts** are built once and reused.
- **Host artefacts** are built per run, cached by content hash.

## Cache keys
Cache keys must include:
- file hash of the input FASTA/FAA
- tool/container versions (or image digests)
- DB version strings (e.g. VFDB release, Uniclust/PDB70 versions)
- key parameters (e.g. k-mer size, e-value threshold)

## Metadata
Each cached artefact directory includes `meta.json` containing:
- inputs + hashes
- tool versions / digests
- parameters
- timestamps

This enables reproducibility and audit trails for clinical-style workflows.
