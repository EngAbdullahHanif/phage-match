# Part 2 product direction

**Decision: Option A.** PhageMatch will focus on a host-range predictor for research. Its intended output is an estimate of the probability of the defined lysis assay outcome for a phage–host pair. The estimate will need validation against held-out assay observations. The current Decision Bundle remains the interface for reporting results and their provenance.

## Initial milestone

Curate the assay workbooks and reconcile their IDs before modeling. Preserve the original category and binary observations, report unresolved IDs, and document the target definition and data eligibility criteria. Use the CPU-only workflow and synthetic fixtures for the initial software checks. A baseline on a prepared, small tabular dataset can run on a CPU. Estimate the cost of any later feature processing separately before provisioning hardware.

## Structural analysis

Structural exploration is optional follow-up work for manual interpretation. Structural comparisons can support hypotheses about mechanism. The default validation and baseline path should have no dependency on bulk folding, structure searches, docking, public MSA services, or a GPU.

## Scope of this decision

This decision sets product direction and the order of work. Assay curation, model development, and validation are separate deliverables with their own acceptance checks.
