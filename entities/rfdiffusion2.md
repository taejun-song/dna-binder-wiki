---
type: entity
title: "RFdiffusion2"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [model, diffusion, protein-design, enzyme-design, baker-lab]
aliases: [RFD2]
---

# RFdiffusion2

A hybrid residue-atom diffusion model that extended RFdiffusion to handle enzyme active-site scaffolding by co-diffusing backbone frames and a small number of catalytic "tip" atoms.

## Overview

RFdiffusion2 (RFD2), published in bioRxiv (2025) by Ahern, Yim et al., addressed the limitation of [[rfdiffusion]] in designing catalytic functions. It introduced residue-level diffusion of backbone frames combined with atom-level diffusion of specified sidechain tip atoms, enabling [[motif-scaffolding]] for enzyme active sites.

## Key design choices

- Tip atoms are a new data type layered onto the residue-level representation
- Diffusion remains at the residue level for all non-tip components
- Cannot model general sidechain-level interactions or non-protein atoms beyond the specified tips

## Limitations

- General atom-level conditioning (H-bond donor/acceptor, atomic burial) not supported
- Cannot handle protein-DNA or protein-small molecule design
- Struggles with motifs spanning more than 4 residue islands (4% pass rate vs 15% for [[rfdiffusion3]])
- Slower inference than RFD3

## Benchmark comparison with RFD3

On the Atomic Motif Enzyme (AME) benchmark of 41 active sites, [[rfdiffusion3]] outperforms RFD2 on 37 cases (90%).
