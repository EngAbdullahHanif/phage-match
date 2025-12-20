# Reproducibility notes

## What makes a run reproducible here
A PhageMatch run is reproducible if you can regenerate the same Decision Bundle outputs from:

- the same host/phage inputs (by hash)
- the same parameters
- the same tool + database versions

## Where this is captured
`rankings/<host_id>/evidence_bundle.json` includes:

- `config_sha256`
- `manifest_hashes`
- `params` snapshot
- `versions` snapshot (tools / container digests / DB version strings)
- per-module statuses

## Cache policy (cache-first)
- **Phage library artefacts** are cached once per `phage_id` (build-time)
- **Host artefacts** are computed on demand and cached per `host_id` (run-time)

Cache keys SHOULD include input hashes + tool/db versions.
