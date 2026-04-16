---
type: entity
title: "RoseTTAFold All-Atom"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion2-paper]]"
tags: [model, structure-prediction, baker-lab]
aliases: [RFAA, RoseTTAFold-AA]
---

# RoseTTAFold All-Atom

A biomolecular structure prediction model that extends RoseTTAFold to handle proteins, nucleic acids, small molecules, and metal ions in a unified all-atom framework.

## Overview

RoseTTAFold All-Atom (RFAA) was published by Krishna, Wang et al. in Science (2024). It generalizes RoseTTAFold's three-track architecture to predict structures of protein-small molecule complexes, protein-nucleic acid complexes, and metalloproteins.

## Relevance to this wiki

RFAA serves as the base architecture for [[rfdiffusion2]]. The RFD2 diffusion process operates on RFAA's representation: residue-level backbone frames augmented with atomic tokens for catalytic sidechains and ligands. RFD2 inherits RFAA's ability to handle non-protein atoms but repurposes it for generative design rather than structure prediction.

[[rfdiffusion3]] later moved away from the RFAA architecture in favor of a simplified [[alphafold3]]-derived U-Net, achieving faster inference with fewer parameters.

## See also

- [[rfdiffusion2]] — the generative model built on RFAA
- [[alphafold3]] — the alternative structure prediction architecture adapted by RFD3
