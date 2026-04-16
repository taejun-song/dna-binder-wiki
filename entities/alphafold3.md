---
type: entity
title: "AlphaFold3"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [model, structure-prediction, deepmind]
aliases: [AF3]
---

# AlphaFold3

A biomolecular structure prediction model by DeepMind/Isomorphic Labs that predicts all-atom structures of proteins, nucleic acids, ligands, and their complexes using a diffusion-based architecture.

## Relevance to RFdiffusion3

[[rfdiffusion3]] adapts and simplifies the AlphaFold3 diffusion module for generative protein design:

- **Shared**: transformer-based U-Net with atom-level diffusion, recycling.
- **Simplified in RFD3**: Pairformer reduced from 48 to 2 layers; triangle attention removed entirely; parameters cut from ~350M to ~168M.
- **Different purpose**: AF3 predicts structures from known sequences; RFD3 generates novel structures from conditioning constraints.

AF3 is also used as the primary evaluation tool in the RFD3 paper — designs are scored by whether AF3 predicts them to fold correctly (pAE, pTM, RMSD metrics).
