# Output contract

## ranking.csv (required)
Columns:
- `host_id`
- `phage_id`
- `rank` (1 = best)
- `confidence_score` (0..1)
- `primary_reason` (string)
- `safety_flags` (string; `none` or comma-separated)

## evidence_bundle.json (required)
Top-level fields:
- `pipeline_version`
- `run_id` (UTC ISO)
- `test_mode` (bool)
- `config_sha256`
- `manifest_hashes` (per manifest)
- `profile`
- `modules` (status + tool versions)
- `params` + `versions` snapshots
- `shortlist` (list of ranked candidates with evidence placeholders)
- `next_best_action` guidance per candidate or for the run

This contract is designed to be UI-ready and audit-friendly.
