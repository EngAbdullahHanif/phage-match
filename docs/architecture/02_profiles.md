# Execution profiles

PhageMatch is designed to **run everywhere** by supporting profiles that keep the *output contract* constant.

## test (runs anywhere)
- No external tools required
- Uses deterministic mocks
- Purpose: CI, onboarding, architecture demonstration

## portable (conda / workstation / HPC)
- Real, lightweight tools via conda/mamba/micromamba
- Typical modules: `sourmash` similarity, `abricate` safety
- No GPU required
- Purpose: baseline ranking MVP for pilot labs

## accelerated (GPU + docker)
- Adds structural evidence (Foldseek) and cached structure prediction (ColabFold)
- Phage library cached; host computed on-demand (and cached)
- Purpose: premium mechanistic evidence and explainability
