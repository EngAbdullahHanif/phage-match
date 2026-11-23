# PhageMatch Part 1 completion plan

Items 1.6–1.9 cover legacy-script portability, retired preprocessing, assay-label leakage, and workspace hygiene. The earlier audit used a separate local snapshot. Apply these follow-up items against the current v0.1 layout and use the mocked workflow as the acceptance baseline.

## 1.6 Make the legacy scripts portable

- Replace the machine-specific Python shebang in `scripts/predict_rbps.py`. Give `scripts/predict_phage_lifestyle.py` an explicit PHACTS executable option, a `PATH` fallback, and an actionable missing-dependency error.
- Retire the duplicate `ffindex` branch in the legacy RBP script. Keep temporary files in the run's output or temporary directory and treat input annotations as read-only. Keep both scripts outside the default workflow.
- **Acceptance check.** Both `--help` commands work from a clean environment. Stub-tool tests cover dependency errors, command routing, and input-directory integrity.

## 1.7 Retire the legacy DNA2Vec feature path

- Keep `legacy/pipeline_main.py` available for reproducing historical outputs. Mark its whole-genome weighted averages as legacy artifacts and exclude them from supported feature inputs.
- Deprecate the per-file PCA, t-SNE, and autoencoder functions. If dimensionality reduction becomes part of a later model, fit preprocessing across samples using only the training rows in each fold.
- **Acceptance check.** A synthetic legacy embedding reproduces the expected output, and the supported workflow emits no DNA2Vec or dimensionality-reduction artifacts.

## 1.8 Keep assay outcomes out of feature inputs

- Treat `phenotypic_metadata.csv` as a label artifact. Document `virulence_index` as a historical placeholder derived from binary outcomes, and `inhibition_efficiency` as derived from assay categories. Retire the placeholder from the supported label export and preserve the original category and binary observations.
- Validate proposed feature tables against an explicit column allowlist. Cover both legacy derived fields and raw label fields in a synthetic regression test.
- **Acceptance check.** The validator accepts approved feature columns and rejects assay-derived columns with an error that names them.

## 1.9 Verify repository hygiene and reproducibility

- Retain the existing Git exclusions and verify that recovery files, real datasets, nested tool checkouts, model weights, and generated outputs stay out of the staged file list. Rotate any exposed recovery codes through the account owner and keep replacement codes in secure storage. [GitHub recovery-code instructions](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication-recovery-methods#generating-a-new-set-of-recovery-codes)
- Track data provenance and checksums with the local inventory. Record the PHACTS revision and preserve any locally sourced artifacts before removing redundant build output. Record useful observations from historical runs in `STATUS.md` and keep raw logs in the ignored `logs/` directory.
- Verify the existing dependency setup from a clean checkout and document the optional requirements for legacy commands separately from the supported workflow.
- **Acceptance check.** A clean checkout passes the mocked workflow and synthetic checks. `STATUS.md` records the unresolved workbook IDs and PHASTER-to-host links from the local inventory.

Do the credential and staging checks first. Then complete 1.6–1.8 and finish with the clean-checkout verification. The earlier inventory fixes in the separate local snapshot are context for these checks.
