---
type: concept
title: "Motif Scaffolding"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [protein-design, enzyme-design, diffusion]
aliases: [functional motif scaffolding, active-site scaffolding]
---

# Motif Scaffolding

The task of generating a protein scaffold that positions a predefined set of functional residues or atoms (the "motif") in a precise spatial arrangement.

## Why it matters

Enzyme active sites, binding epitopes, and catalytic triads require specific atoms at exact 3D coordinates. A scaffold must fold stably while presenting those atoms in the required geometry. This is one of the hardest challenges in computational protein design because the motif constrains both local chemistry and global fold.

## Approaches

### Residue-level (RFD1 / RFD2)

[[rfdiffusion]] and [[rfdiffusion2]] provide motif coordinates at the residue level. RFD2 introduced a hybrid residue-atom representation to handle catalytic "tip atoms," but the rest of the protein remained residue-level, limiting the types of motifs that could be scaffolded.

### All-atom (RFD3)

[[rfdiffusion3]] scaffolds motifs at full atomic resolution. For each catalytic residue, an extra token containing the fixed atom coordinates is appended to the diffused tokens. The model is trained to place one of the diffused sidechain sets on top of the fixed motif atoms. This allows scaffolding of:

- Multi-residue-island active sites (up to 7 residue islands demonstrated)
- Symmetric motifs across chains (C2 symmetry demonstrated)
- Motifs with specific hydrogen-bond requirements

## Benchmark: Atomic Motif Enzyme (AME)

The AME benchmark measures scaffolding success on 41 PDB active sites. [[rfdiffusion3]] outperforms [[rfdiffusion2]] on 37/41 cases (90%), with the largest gains on motifs with more than 4 residue islands (15% vs 4% pass rate).

## See also

- [[all-atom-diffusion]] — the underlying generative framework
- [[rfdiffusion3]] — current state-of-the-art for motif scaffolding
