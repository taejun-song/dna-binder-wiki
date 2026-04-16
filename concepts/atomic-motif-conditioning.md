---
type: concept
title: "Atomic Motif Conditioning"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion2-paper]]"
tags: [diffusion, enzyme-design, conditioning]
aliases: [motif representation modes]
---

# Atomic Motif Conditioning

The three modes by which [[rfdiffusion2]] encodes catalytic functional-group geometry as input to the diffusion process, varying in how much information the user provides versus the model infers.

## The three modes

### 1. Backbone motif

The user provides the full residue identity, sidechain rotamer, and sequence index for each catalytic residue. This is equivalent to classical [[motif-scaffolding]] as done in [[rfdiffusion]]. The model only needs to generate the surrounding scaffold.

### 2. Atomic motif

The user provides atom coordinates and the sequence index (position in the protein) but the model infers the sidechain rotamer. This gives the network freedom to explore rotamer space while respecting the user's placement of catalytic residues in the sequence.

### 3. Unindexed atomic motif

The user provides only the atom coordinates of the functional groups — no residue identity, no rotamer, no sequence index. The model infers all three. This is the most flexible mode and produces the greatest scaffold diversity, because the network can place the catalytic residues anywhere in the generated sequence.

## Comparison

| Property | Backbone | Atomic | Unindexed |
|---|---|---|---|
| Residue identity | Provided | Provided | Inferred |
| Rotamer | Provided | Inferred | Inferred |
| Sequence index | Provided | Provided | Inferred |
| Scaffold diversity | Lowest | Medium | Highest |
| Search space | L!/(L-M)! | M^(rotamer states) | L!/(L-M)! x M^(rotamer states) |

Where L = protein length, M = number of motif residues.

## Performance on AME benchmark

Evaluated on the AME benchmark (41 active sites), the "inferred" (unindexed) mode achieves the best overall performance, surpassing even the use of native rotamers and sequence indices. At ≥4 residue islands, [[rfdiffusion]] fails entirely while [[rfdiffusion2]] with inferred mode still finds solutions.

## Additional conditioning

Beyond motif mode, RFD2 supports:

- **RASA conditioning**: control ligand burial by specifying solvent-accessible surface area per atom (exposed / partial / buried).
- **ORI pseudo-atom**: a special token that specifies the approximate center of mass, controlling the orientation of the active site relative to the protein core.
- **Partial ligand**: provide only part of the substrate to guide design without fully constraining ligand geometry.

## See also

- [[theozyme]] — the idealized active-site input that these modes encode
- [[rfdiffusion2]] — the model implementing these modes
- [[motif-scaffolding]] — the broader task
