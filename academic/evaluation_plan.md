# Evaluation plan (v0.1 - v0.x)

This plan is designed to answer three stakeholder questions:

- Scientist: is the method comparable and reproducible?
- Lab operator: does it reduce bench time by prioritizing likely hits?
- Partner/investor: is the architecture scalable and defensible?

## Datasets
Minimum viable evaluation requires:
- host isolates with genomes (and ideally proteomes)
- a phage library with genomes
- wet-lab outcomes per host-phage: hit/no-hit, and ideally EOP / plaque morphology

If historical data exists, the pipeline should be run as-is against frozen manifests and compared to outcomes.

## Primary metrics
- Top-k hit rate: fraction of hosts with at least 1 true hit in the top k candidates (k in {5,10,20})
- Mean reciprocal rank (MRR): rewards putting true hits near the top
- Work saved proxy: (library size - rank of first hit) / library size

## Safety evaluation (separate axis)
Safety is not a predictive accuracy metric; it is a screening metric.
Track:
- fraction of candidates flagged for review
- concordance with expert curation (manual review subsets)

## Ablations (comparability)
Run the same frozen input set with modules toggled:
- similarity-only
- structural-only (where available)
- similarity + structural
- with/without safety penalties

Record each run as a Decision Bundle and compare metrics.

## Reproducibility requirements
Every evaluation must archive:
- `config.yaml` used (or config hash)
- manifests used (+ hashes)
- tool versions / container digests
- database versions (VFDB, Foldseek, etc.)

The Decision Bundle is the default storage unit.
