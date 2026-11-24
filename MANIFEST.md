# Local data and tool provenance

Keep source workbooks, sequence files, generated reports, and real run outputs outside Git. Track code, configuration, schemas, and synthetic test fixtures in Git. Use a private backup location approved for the data.

| Local path | Contents |
| --- | --- |
| `data/meta_data/` | Source workbooks and generated ID crosswalk |
| `data/genomes_id/`, `data/phage_genome/`, `data/phaster_results/` | Local sequence files and PHASTER provenance |
| `data/interim/`, `data/processed/`, `reports/` | Derived outputs kept locally |
| `logs/2025-06-server-run/` | Historical server logs when available in the local workspace |

Generate checksums from the project root. Keep the checksum list with the private copy.

```sh
find data -type f ! -name .DS_Store ! -name '~$*' ! -name SHA256SUMS -print0 \
  | LC_ALL=C sort -z | xargs -0 shasum -a 256 > data/SHA256SUMS
shasum -a 256 -c data/SHA256SUMS
```

Copy to the approved backup destination using `rsync -a data/ "$PHAGEMATCH_DATA_BACKUP/"` after setting `PHAGEMATCH_DATA_BACKUP` to that destination. Verify the checksums from a directory containing the restored `data/` tree.

## Optional legacy tool

SHA `5ce29fcef89180af905b9f968d402c30f47befaf` identifies the historical PHACTS source checkout. Keep it external to the repository and configure the existing legacy wrapper with `--phacts` if needed. The core environment and assay inventory do not import this package. Preserve locally sourced artifacts in the private backup before removing generated build products.
