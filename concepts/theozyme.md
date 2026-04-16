---
type: concept
title: "Theozyme"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion2-paper]]"
tags: [enzyme-design, computational-chemistry, active-site]
aliases: [theoretical enzyme, theozymes]
---

# Theozyme

An idealized arrangement of catalytic functional groups around a reaction transition state, used as the starting point for de novo enzyme design.

## Definition

A theozyme (theoretical enzyme) describes the minimal chemical geometry needed to catalyze a target reaction: the catalytic residues, their spatial relationship to the substrate, any cofactors, and optionally the reaction transition state itself. Theozymes can be derived from:

- **Crystal structures**: extracting the active-site geometry from a known enzyme (e.g., PDB structures).
- **Quantum chemistry / DFT**: computing the optimal transition-state geometry and the catalytic groups that stabilize it, without requiring a known enzyme.

## Role in enzyme design pipelines

The theozyme serves as the input motif for [[motif-scaffolding]]. The design pipeline then generates a protein scaffold that positions these functional groups in the specified geometry:

1. Define the theozyme (from crystal structure or DFT).
2. Generate scaffolds using a diffusion model ([[rfdiffusion2]] or [[rfdiffusion3]]).
3. Assign sequences using [[ligandmpnn]].
4. Validate with structure prediction ([[alphafold3]] or Chai).

## Theozyme sources in RFD2 experiments

[[rfdiffusion2]] validated on both types:

- **Crystal-structure theozymes**: retroaldolase (PDB 6SU3) and cysteine hydrolase (PDB 5K7V) — active-site geometry taken directly from solved structures.
- **DFT-computed theozymes**: three zinc hydrolase designs where DFT identified the optimal transition-state geometry for carbon-carbon bond formation or ester hydrolysis, without prior knowledge of a natural enzyme.

The DFT approach is particularly significant because it enables enzyme design for reactions with no known biological catalyst.

## See also

- [[motif-scaffolding]] — the scaffolding task that consumes theozymes as input
- [[atomic-motif-conditioning]] — the representation modes for encoding theozymes in RFD2
