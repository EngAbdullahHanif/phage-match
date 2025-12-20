# PhageMatch - Decision support for phage selection

## Problem
Phage therapy requires matching the right phages to a specific bacterial isolate. Today this often means broad empirical screening across phage libraries, which is slow, labour-heavy, and hard to standardise.

## Solution
PhageMatch is a decision-support workflow that returns:
- a ranked shortlist of phages to test first
- safety flags
- an evidence bundle with traceability and audit fields

## Why now
- AMR is accelerating
- phage centres and banks are scaling
- sequence/structure tooling enables practical triage layers

## Moat
- workflow + audit trail + cache-first architecture
- feedback loop: wet-lab outcomes improve future rankings (data moat)

## What this repo is
A clean architecture stub that demonstrates the pipeline contracts and the Decision Bundle output. Feature modules can be mocked (demo) or run for real (portable/accelerated profiles) without changing outputs.

## Pilot ask (what we need from a partner lab)
- isolate genome/proteome (or sequencing output)
- access to a phage library catalogue (genomes)
- optional historical host-range results for evaluation

## What the partner gets
- ranked shortlist + evidence bundle for each isolate
- reproducible run metadata (hashes, versions, parameters)
- roadmap to structural evidence and learning loop
