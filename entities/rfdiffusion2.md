---
type: entity
title: "RFdiffusion2"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
  - "[[rfdiffusion2-paper]]"
tags: [model, diffusion, protein-design, enzyme-design, baker-lab]
aliases: [RFD2]
---

# RFdiffusion2

A hybrid residue-atom diffusion model that designs enzymes directly from atomic functional-group geometries without requiring predefined residue order or rotamer selection.

## Overview

RFdiffusion2 (RFD2), published in Nature Methods (January 2026) by Ahern, Yim, Tischer et al. from [[david-baker]]'s lab, was the first generative model to scaffold enzyme active sites from minimal atomic motifs. It addressed the limitation of [[rfdiffusion]] in designing catalytic functions by introducing a hybrid representation that co-diffuses backbone residue frames and catalytic sidechain atoms.

## Architecture

- **Base**: built on [[rosettafold-all-atom]] (RFAA), inheriting its three-track architecture and ability to handle non-protein atoms.
- **Representation**: backbone residues as rigid-body frames (translation + rotation); catalytic residues as atomic motif tokens with explicit sidechain atom coordinates; ligands/substrates as fixed context atoms.
- **Diffusion process**: at t=0, backbone frames are drawn from a noise distribution; atomic motif "tail" atoms connect to the backbone. Over the trajectory, unindexed residues match to indexed backbone positions. By t=1, all atoms are resolved.
- **Code**: open source at github.com/RosettaCommons/RFdiffusion2.

## Motif conditioning modes

RFD2 introduced three [[atomic-motif-conditioning]] modes with increasing degrees of freedom:

1. **Backbone motif** — residue identity, rotamer, and sequence index all provided (classical approach).
2. **Atomic motif** — coordinates and index provided, rotamer inferred by the model.
3. **Unindexed atomic motif** — only atom coordinates provided; identity, rotamer, and index all inferred. Produces the greatest scaffold diversity.

## Additional conditioning

- **RASA** — solvent-accessible surface area labels to control ligand burial (exposed / partial / buried).
- **ORI pseudo-atom** — specifies approximate center of mass to control active-site orientation relative to the protein core.
- **Partial ligand** — provide only part of the substrate to guide design without fully constraining geometry.

## AME benchmark

The Atomic Motif Enzyme (AME) benchmark tests scaffolding on 41 active sites from the M-CSA database, spanning EC classes 1–5. Results:

- RFD2 successfully scaffolds all 41 active sites; [[rfdiffusion]] scaffolds only 16.
- RFD2 has higher success rates across all residue-island categories (1–7 islands).
- The unindexed atomic motif mode with inferred rotamers and indices achieves the best performance overall.
- At ≥4 residue islands, RFD1 fails entirely while RFD2 still finds solutions.

Note: [[rfdiffusion3]] later outperformed RFD2 on 37/41 AME cases using a stricter Chai-predicted all-atom RMSD < 1.5 Å criterion. The success-rate gap is partly due to different evaluation criteria between the two papers.

## Experimental validation

RFD2 designed functional enzymes for 5 reactions, with active candidates found after testing fewer than 96 sequences each:

| Reaction | Theozyme source | PDB | k_cat/K_m (M⁻¹s⁻¹) |
|---|---|---|---|
| Retroaldolase | Crystal structure | 6SU3 | 6.37 |
| Cysteine hydrolase | Crystal structure | 5K7V | 250 |
| Zinc hydrolase (4MU-butyrate) | DFT | 2ZH1 | 77 |
| Zinc hydrolase (4MU-PhAc) | DFT | 4WM8 | 16,000 |
| Zinc hydrolase (4MU-PhAc) | DFT | 2E14 | 53,000 |

The three DFT-derived [[theozyme]] designs are notable because they required no prior knowledge of a natural enzyme for the target reaction.

## Limitations

- Cannot model general sidechain-level interactions beyond the catalytic motif (the rest of the protein is residue-level).
- Cannot handle protein-DNA or protein-small molecule binder design.
- Slower inference than [[rfdiffusion3]] due to the RFAA-inherited architecture.

## Relation to other models

- [[rfdiffusion]] (RFD1): residue-level only; RFD2 extends it with atomic motif handling.
- [[rfdiffusion3]] (RFD3): full [[all-atom-diffusion]]; subsumes RFD2's capabilities with unified atom-level treatment and faster inference.
- [[rosettafold-all-atom]]: the structure prediction model whose architecture RFD2 adapts for generative design.

## See also

- [[motif-scaffolding]] — the core task RFD2 addresses
- [[atomic-motif-conditioning]] — the three motif representation modes
- [[theozyme]] — the idealized active-site inputs used in RFD2 experiments
