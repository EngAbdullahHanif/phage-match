# Assay quality and ID provenance

The assay inventory writes `reports/assay_qc.csv` with workbook, worksheet, Excel cell, severity, issue code, and detail. Review entries flag observations with no host ID, populated cells under unnamed columns, or header IDs that are absent from the other worksheet. A duplicate observation points to the first cell with that normalized pair. Missing sheets, duplicate headers, duplicate observations, and invalid scores block the export. The QC report is written first so those issues can be reviewed without replacing the prior inventory and observation exports.

## Review local ID mappings

Copy `config/assay_aliases.example.tsv` into a private data folder and pass that file as `--aliases`. Use one row per candidate mapping and include its role (`host` or `phage`), source ID, target file stem, evidence, and review status.

| Status | Effect |
| --- | --- |
| `pending` | Records a candidate for review. A candidate by itself leaves the source ID unresolved. |
| `confirmed` | Uses an alias with nonempty evidence. A disagreement with an exact file stem or another confirmed target produces a `conflict` entry. |
| `rejected` | Records the review decision without using the candidate for coverage. |

An exact file-stem match remains eligible while an alternate mapping is pending. The previous four-column alias format remains compatible and treats entries with evidence as already confirmed. Use the reviewed format for new decisions. Keep input workbooks, completed aliases, and generated reports local.

Run the audit with `--allow-unresolved` to generate reports during review. Omit that flag for strict ID validation. Workbook errors are blocking in both modes. The inventory separates observations with confirmed local IDs from observations still needing review.

## Verify on another machine

From a clean checkout with Conda installed, run:

```sh
conda env create --file environment.yml
conda run -n phagematch python -m pytest -q
```

The test suite creates synthetic workbooks and placeholder files in temporary directories. Record the platform, Git revision, and result in the handoff after the check. [Assay-owner checklist](label_definition.md)
