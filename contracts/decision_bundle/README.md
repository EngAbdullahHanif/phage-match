# Decision Bundle contract

This repo's shared core is the Decision Bundle:

- `ranking.csv` - what a lab operator acts on (spreadsheet-friendly)
- `evidence_bundle.json` - what a scientist/auditor/partner inspects (UI-ready + provenance)

Both Layer A (academic artefact) and Layer B (product workflow) must produce and consume these artefacts without breaking schema.

## Required outputs per host run

```
rankings/<host_id>/ranking.csv
rankings/<host_id>/evidence_bundle.json
```

## ranking.csv

Required columns:

- `host_id`
- `phage_id`
- `rank` (1 = best)
- `confidence_score` (0..1)
- `primary_reason` (human-readable string)
- `safety_flags` (`none` or delimiter-separated flags)

## evidence_bundle.json

JSON Schema: `evidence_bundle.schema.json`

Top-level fields:

- `pipeline_version`
- `run_id` (UTC ISO-8601 recommended)
- `profile` (e.g. `test`, `portable`, `accelerated`)
- `test_mode` (bool)
- `config_sha256`
- `manifest_hashes` (hashes for `manifests/phages.tsv` + `manifests/hosts.tsv`)
- `modules` (status/tool/tool_version for `similarity`, `safety`, `structural`)
- `params` + `versions` snapshots (for audit + comparability)
- `shortlist` (ranked candidates with embedded evidence)

## Example

Canonical demo bundle lives at `demo_outputs/H001/`.
`examples/` only contains a pointer to avoid drift.
