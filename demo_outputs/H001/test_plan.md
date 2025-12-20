# Test Plan (Demo)

This repository is an **architecture stub** for PhageMatch: it demonstrates the end-to-end *decision bundle* workflow
(host isolate → ranked shortlist → evidence bundle → audit trail), with mock feature modules.

## Suggested wet-lab validation order (example)
1) P001 — run plaque assay; if positive, EOP; then consider cocktail design
2) P002 — run if P001 fails or if temperate risk is acceptable under your protocol
3) P003 — deprioritised due to safety flags and weak evidence

> Note: In real runs, this file is generated from the evidence bundle.
