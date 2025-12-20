# Feature contracts

Feature modules write *per host × phage* feature artefacts with stable schemas.

## similarity.json (example)
Required:
- `host_id`, `phage_id`
- `metric` (e.g., `containment`, `jaccard`, `distance`)
- `value` (float)
- `tool`, `tool_version`
- `status`: `ok | mocked | skipped | unavailable`
- optional `reason` if skipped

## safety.json (minimum schema)
Required:
- `phage_id`
- `vfdb_hits` (int)
- `integrase_like` (bool)
- `tRNA_count` (int)
- `flags` (list[str])
- `tool`, `tool_version`, `status`

## structural.json (Foldseek summary)
Required:
- `host_id`, `phage_id`
- `hit_count` (int)
- `best_evalue` (float)
- optional: `best_bitscore`, `top_targets` (list)
- `tool`, `tool_version`, `status`

The aggregator must tolerate missing features and apply defaults (with explicit evidence statuses).
