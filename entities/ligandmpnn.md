---
type: entity
title: "LigandMPNN"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [model, sequence-design, protein-design, baker-lab]
aliases: []
---

# LigandMPNN

An extension of [[proteinmpnn]] for atomic-context-conditioned protein sequence design, capable of designing sequences in the presence of small molecules, nucleic acids, and other non-protein atoms.

## Role in the RFdiffusion3 pipeline

When [[rfdiffusion3]] generates structures that include non-protein components (DNA, ligands), LigandMPNN replaces ProteinMPNN for the sequence-design step. It conditions on the ligand/DNA coordinates to produce sequences that are more likely to form productive interactions with the non-protein partner.

Published by Dauparas et al. in Nature Methods (2025).
