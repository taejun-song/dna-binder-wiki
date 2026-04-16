---
type: concept
title: "Motif Scaffolding"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
  - "[[rfd3-genome-editing-binders]]"
  - "[[rfdiffusion2-paper]]"
tags: [protein-design, enzyme-design, diffusion]
aliases: [functional motif scaffolding, active-site scaffolding]
---

# Motif Scaffolding

The task of generating a protein scaffold that positions a predefined set of functional residues or atoms (the "motif") in a precise spatial arrangement.

## Why it matters

Enzyme active sites, binding epitopes, and catalytic triads require specific atoms at exact 3D coordinates. A scaffold must fold stably while presenting those atoms in the required geometry. This is one of the hardest challenges in computational protein design because the motif constrains both local chemistry and global fold.

## Approaches

### Residue-level (RFD1)

[[rfdiffusion]] provides motif coordinates at the residue level only — backbone frames with fixed sequence indices and rotamers. This limits scaffolding to motifs where the exact residue placement is known in advance.

### Hybrid residue-atom (RFD2)

[[rfdiffusion2]] introduced three [[atomic-motif-conditioning]] modes: backbone motif (classical), atomic motif (rotamer inferred), and unindexed atomic motif (both rotamer and sequence index inferred). The unindexed mode produces the greatest scaffold diversity because it lets the model decide where to place catalytic residues in the sequence. Input motifs can come from crystal structures or DFT-computed [[theozyme]]s.

### All-atom (RFD3)

[[rfdiffusion3]] scaffolds motifs at full atomic resolution. For each catalytic residue, an extra token containing the fixed atom coordinates is appended to the diffused tokens. The model is trained to place one of the diffused sidechain sets on top of the fixed motif atoms. This allows scaffolding of:

- Multi-residue-island active sites (up to 7 residue islands demonstrated)
- Symmetric motifs across chains (C2 symmetry demonstrated)
- Motifs with specific hydrogen-bond requirements

## Benchmark: Atomic Motif Enzyme (AME)

The AME benchmark measures scaffolding success on 41 active sites from the M-CSA database, spanning EC classes 1–5 with 1–7 residue islands. Key results across models:

- [[rfdiffusion]]: scaffolds 16/41 sites; fails at ≥4 residue islands.
- [[rfdiffusion2]]: scaffolds all 41/41 sites; unindexed atomic motif mode achieves best diversity.
- [[rfdiffusion3]]: outperforms RFD2 on 37/41 cases (using Chai-predicted all-atom RMSD < 1.5 Å criterion); 15% vs 4% pass rate on >4 islands.

Note: the RFD2 and RFD3 papers use slightly different success criteria, so cross-paper comparisons should be interpreted with care.

## Re-scaffolding (specblock)

In practice, initial [[rfdiffusion3]] designs can be further diversified by re-scaffolding specific regions — for example, fixing the major-groove DNA recognition interface and re-diffusing the rest of the protein. This "specblock" protocol is used in the [[dna-binder-design-targets|genome editing binder dataset]], where it generates variant scaffolds for the same DNA-binding motif.

## See also

- [[all-atom-diffusion]] — the underlying generative framework
- [[rfdiffusion3]] — current state-of-the-art for motif scaffolding
- [[dna-binder-design-targets]] — genome editing targets using motif re-scaffolding
