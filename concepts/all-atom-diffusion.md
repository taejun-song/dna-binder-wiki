---
type: concept
title: "All-Atom Diffusion"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [diffusion, protein-design, generative-model]
aliases: [atom-level diffusion, atomic diffusion]
---

# All-Atom Diffusion

Generative diffusion over individual atom coordinates rather than residue-level representations, enabling explicit modeling of sidechain geometry and non-protein atoms.

## Motivation

Traditional protein diffusion models such as [[rfdiffusion]] operate at the residue level, placing one pseudo-atom (typically Cα) per amino acid. This is sufficient for backbone topology but cannot capture sidechain rotamers, ligand contacts, hydrogen-bond geometry, or nucleic-acid interactions. All-atom diffusion closes this gap by making every heavy atom a first-class diffused coordinate.

## Representation

[[rfdiffusion3]] represents each residue as 14 atoms: 4 backbone atoms plus 10 sidechain atom slots. Residues with fewer than 10 sidechain atoms fill the remaining slots with virtual atoms placed on Cβ (Cα for glycine). The terminal oxygen of serine and the sulfur of cysteine are treated as distinct virtual atoms so the network can distinguish them.

## Relation to residue-level diffusion

| Property | Residue-level | All-atom |
|---|---|---|
| Diffused unit | Cα (or backbone frame) | Every heavy atom |
| Sidechain modeling | Post-hoc (e.g., packing) | Joint with backbone |
| Non-protein atoms | Not natively supported | Ligands, DNA, cofactors modeled in the same coordinate space |
| Conditioning granularity | Residue hotspots | Atom-level hotspots, H-bond donor/acceptor, RASA per atom |

## Trade-offs

All-atom diffusion increases the token count per residue (14× vs 1×), demanding architectural choices to keep compute tractable. [[rfdiffusion3]] addresses this with sparse attention within residues and cross-attention between atom and token tracks, omitting the expensive triangle attention used in [[alphafold3]].

## See also

- [[classifier-free-guidance]] — used in RFD3 to improve conditioning adherence at the atom level
- [[motif-scaffolding]] — benefits from atom-level precision for active-site placement
