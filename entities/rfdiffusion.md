---
type: entity
title: "RFdiffusion"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [model, diffusion, protein-design, baker-lab]
aliases: [RFD1, RFdiffusion1]
---

# RFdiffusion

The first diffusion-based model for de novo protein structure generation, operating at the residue level to produce protein backbone coordinates.

## Overview

RFdiffusion (RFD1), published in Nature (2023) by Watson, Juergens, Bennett et al. from [[david-baker]]'s lab, demonstrated that denoising diffusion over residue-level representations could generate novel, designable protein backbones. It inherited much of the RoseTTAFold architecture.

## Capabilities

- Unconditional backbone generation
- Protein binder design (residue-level hotspot conditioning)
- Symmetric oligomer design (via symmetric noise initialization)
- Fold-conditioned generation

## Limitations

- Residue-level representation cannot model sidechain geometry or non-protein atoms
- Cannot design specific interactions with small molecules, nucleic acids, or cofactors
- Slower inference than [[rfdiffusion3]] due to inherited RoseTTAFold architecture

## Successor models

- [[rfdiffusion2]] added hybrid residue-atom handling for catalytic tip atoms
- [[rfdiffusion3]] moved to full [[all-atom-diffusion]], subsuming RFD1's capabilities with greater diversity and speed
