# Output contract

## ranking.csv (required)
Columns:
- `host_id`
- `phage_id`
- `rank` (1 = best)
- `confidence_score` (0..1)
- `primary_reason` (string)
- `safety_flags` (string; `none` or delimiter-separated)

## evidence_bundle.json (required)
Top-level fields:
- `pipeline_version`
- `run_id` (UTC ISO)
- `profile`
- `test_mode` (bool)
- `config_sha256`
- `manifest_hashes` (per manifest)
- `modules` (status + tool versions)
- `params` + `versions` snapshots
- `shortlist` (ranked candidates with embedded evidence)

Schema: `contracts/decision_bundle/evidence_bundle.schema.json`

This contract is designed to be UI-ready and audit-friendly.

## test_plan.md (optional)
- Lightweight markdown summary of top-ranked candidates and next actions.
- Generated from `ranking.csv` + `evidence_bundle.json`.
