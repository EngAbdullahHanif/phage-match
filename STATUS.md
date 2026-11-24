# PhageMatch status

The supported next milestone is curating assay observations and checking local file coverage. Product direction and the scope of the earlier cleanup are recorded in the Part 2 decision and the Part 1 completion plan. The historical run notes document earlier experiments.

## Reproduce the assay audit

Create the core environment with `conda env create --file environment.yml` and activate it with `conda activate phagematch`. You can also install `requirements.txt` into a Python 3.12 virtual environment. Run `python -m pytest` for the synthetic checks. `requirements-ml.txt` lists optional ML dependencies separately. No model weights are needed for this milestone.

Run the inventory from the root of the workspace containing the local inputs. Pass `--aliases` with a reviewed TSV containing `role`, `source_id`, `target_id`, and `evidence` if documented aliases are available.

```sh
python scripts/build_interactions.py \
  'data/meta_data/SST_ E. coli and Salmonella phages.xlsx' \
  data/meta_data/sst_e_coli_phages.xlsx
```

The CLI writes `data/interim/interactions.csv`, `data/meta_data/id_crosswalk.csv`, and `reports/data_inventory.md`. It returns an error if the crosswalk includes unresolved IDs. Use `--allow-unresolved` for a reporting-only run. File coverage is reported independently of assay target definition and eligibility. See [data provenance](MANIFEST.md) and the [label definition](docs/label_definition.md).

## Feature table checks

Use `python scripts/validate_feature_columns.py path/to/table.csv` to check a CSV or TSV header against `features_manifest.yaml`. A reviewed registration records the data source, dtype, and role. The validator rejects unregistered names and the historical assay-derived columns. The manifest starts with no feature registrations.

## Work remaining

- Review the unresolved IDs and workbook anomalies in the private inventory report.
- Confirm the assay definition and eligibility rules before interpreting the number of usable observations.
- The account owner handles recovery-code rotation. Keep recovery files out of Git.
- Verify the Conda setup and synthetic checks on a second machine.
