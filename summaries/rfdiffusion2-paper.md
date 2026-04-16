---
type: source-summary
title: "RFdiffusion2 Paper"
created: 2026-04-16
updated: 2026-04-16
sources: []
tags: [paper, enzyme-design, diffusion, protein-design]
aliases: []
source_file: "../raw/papers/rfdiffusion2.pdf"
source_kind: pdf
source_date: 2025-12-03
---

# RFdiffusion2 Paper

Published article introducing RFdiffusion2, a hybrid residue-atom diffusion model for de novo enzyme design from atomic functional-group geometries.

## Bibliographic details

- **Title**: Atom-level enzyme active site scaffolding using RFdiffusion2
- **Authors**: Woody Ahern, Jason Yim, Doug Tischer, Saman Salike, Seth M. Woodbury, Donghyo Kim, Indrek Kalvet, Yakov Kipnis, Brian Coventry, Han Raut Altae-Tran, Magnus S. Bauer, Regina Barzilay, Tommi S. Jaakkola, Rohith Krishna, David Baker
- **Venue**: Nature Methods, Vol 23, January 2026, pp 96–105
- **DOI**: 10.1038/s41592-025-02975-x
- **Published online**: 3 December 2025
- **License**: CC-BY-NC-ND 4.0
- **Pages read**: 1–14 (full article including reporting summary)

## Problem statement

Existing AI-based enzyme design methods require predefined residue positions and rely on reverse-building residue backbones from side-chain placements, limiting design flexibility. The paper asks whether a generative model can design enzymes directly from atomic functional-group geometries — [[theozyme]]s — without specifying residue order or performing inverse rotamer generation.

## Key contributions

1. **Hybrid residue-atom diffusion** — built on [[rosettafold-all-atom]], co-diffusing backbone frames and catalytic sidechain atoms. The model resolves unindexed atomic motifs to specific sequence positions during the diffusion trajectory.

2. **Three [[atomic-motif-conditioning]] modes** — backbone (classical), atomic (rotamer inferred), and unindexed atomic (both rotamer and index inferred). Unindexed mode achieves greatest scaffold diversity.

3. **Additional conditioning** — RASA for ligand burial control, ORI pseudo-atom for center-of-mass orientation, partial ligand specification.

4. **AME benchmark** — 41 active sites from M-CSA. [[rfdiffusion2]] scaffolds all 41; [[rfdiffusion]] scaffolds only 16. RFD2 dominates across all residue-island categories, especially at ≥4 islands where RFD1 fails entirely.

5. **Experimental validation** — functional enzymes for 5 reactions:
   - Retroaldolase (PDB 6SU3): k_cat/K_m = 6.37 M⁻¹s⁻¹
   - Cysteine hydrolase (PDB 5K7V): k_cat/K_m = 250 M⁻¹s⁻¹
   - Zinc hydrolase, 4MU-butyrate (PDB 2ZH1): k_cat/K_m = 77 M⁻¹s⁻¹
   - Zinc hydrolase, 4MU-PhAc (PDB 4WM8): k_cat/K_m = 16,000 M⁻¹s⁻¹
   - Zinc hydrolase, 4MU-PhAc (PDB 2E14): k_cat/K_m = 53,000 M⁻¹s⁻¹

   Three of these used DFT-computed theozymes with no prior knowledge of a natural enzyme.

## Figures

- **Fig 1**: RFD2 overview — theozyme input, diffusion trajectory, design-to-prediction pipeline.
- **Fig 2**: conditioning — motif representations (backbone / atomic / unindexed), RASA, ORI, partial ligand.
- **Fig 3**: AME benchmark results — EC distribution, success rates by residue islands, per-site results, TM-score distribution.
- **Fig 4**: experimental results — 5 enzyme designs with kinetics plots.

## Relation to other sources

- The [[rfdiffusion3-paper]] later reported RFD3 outperforming RFD2 on 37/41 AME cases, but uses a stricter evaluation criterion (Chai-predicted all-atom RMSD < 1.5 Å) than this paper's own filters. Both papers agree that atomic-level motif handling is essential for complex active sites.
- The cysteine hydrolase reaction appears in both papers: RFD2 achieved k_cat/K_m = 250 M⁻¹s⁻¹; [[rfdiffusion3]] later achieved 3557 M⁻¹s⁻¹ on the same reaction using the Ulp-1 crystal structure.

## Wiki pages generated

- [[theozyme]], [[atomic-motif-conditioning]], [[rosettafold-all-atom]]
- Major update to [[rfdiffusion2]]
