# Decision Bundle interface

The current interface is a set of files. The versioned repository includes a mocked Decision Bundle in `demo_outputs/H001/` for testing consumers and demonstrating the format.

| File | Purpose |
| --- | --- |
| `ranking.csv` | Ordered entries with IDs, rank, a score, and evidence summaries |
| `evidence_bundle.json` | Run provenance, profile, module status, and per-entry evidence |
| `test_plan.md` | Optional Markdown summary generated from the two bundle files |

Check `test_mode` and module status before using a bundle. The demo uses mock data. Its `confidence_score` is a demonstration score on a 0–1 scale. The project has no validated probability output, abstention policy, prediction CLI, or HTTP service. [Output contract](architecture/05_output_contract.md)

## Validate the bundled example

Run this from a Git checkout with the pinned core environment:

```sh
python scripts/validate_decision_bundle.py \
  --ranking demo_outputs/H001/ranking.csv \
  --evidence demo_outputs/H001/evidence_bundle.json \
  --schema contracts/decision_bundle/evidence_bundle.schema.json
```

A successful check prints `VALIDATION OK`. It checks CSV headers and basic types plus the JSON schema. Use the sample bundle to test parsing, provenance display, and consumer compatibility.

## Read a structural alignment table

The standalone `scripts/parse_foldseek.py` accepts Foldseek's default 12-column `easy-search` TSV and adds a column header. A zero-byte input becomes a header-only TSV. A row with an unexpected number of columns produces an error with its line number. The synthetic smoke test exercises the file format with a generated helix and a single CPU thread. [Foldseek tabular output](https://github.com/steineggerlab/foldseek#tab-separated)

A structural alignment reports structural similarity. It supplies no binding or assay outcome measurement. The parser is independent of the prediction workflow.
