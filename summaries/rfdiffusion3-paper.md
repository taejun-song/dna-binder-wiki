---
type: source-summary
title: "RFdiffusion3 Paper"
created: 2026-04-16
updated: 2026-04-16
sources: []
tags: [paper, preprint, diffusion, protein-design]
aliases: []
source_file: "../raw/papers/rfdiffusion3.pdf"
source_kind: pdf
source_date: 2025-11-19
---

# RFdiffusion3 Paper

Preprint introducing RFdiffusion3, an all-atom diffusion model for de novo protein design in the context of ligands, nucleic acids, and other non-protein biomolecules.

## Bibliographic details

- **Title**: De novo Design of All-atom Biomolecular Interactions with RFdiffusion3
- **Authors**: Jasper Butcher, Rohith Krishna, Raktim Mitra, Rafael I. Brent, Yanjing Li, … Frank DiMaio, David Baker (corresponding: rohith@uw.edu, dabaker@uw.edu)
- **Venue**: bioRxiv preprint (doi: 10.1101/2025.09.18.676967), posted 2025-11-19
- **License**: CC-BY 4.0
- **Pages read**: 1–20 (full main text, figures, and references)

## Problem statement

Most deep-learning protein design methods operate at the residue level and cannot model sidechain-level interactions with non-protein atoms. The paper asks whether a unified [[all-atom-diffusion]] model can handle protein binder design, DNA-binding protein design, small-molecule binder design, and enzyme design within a single framework.

## Key contributions

1. **All-atom diffusion architecture** — a transformer-based U-Net adapted from [[alphafold3]]'s diffusion module, reduced to ~168M parameters by shrinking the Pairformer (48→2 layers) and removing triangle attention. Each residue is represented as 14 atoms (4 backbone + 10 sidechain).

2. **Rich conditioning vocabulary** — atom-level hotspots, hydrogen-bond donor/acceptor labels, solvent-accessible surface area (RASA), center-of-mass positioning, symmetric noise, and functional [[motif-scaffolding]]. All conditionings benefit from [[classifier-free-guidance]].

3. **In silico benchmarks**:
   - Protein binders: outperforms [[rfdiffusion]] on 4/5 targets; ~8.2 vs 1.4 successful backbone clusters per target.
   - DNA binders: 8.67% monomeric / 6.67% dimeric pass rate; jointly predicts DNA conformation.
   - Small-molecule binders: outperforms RFdiffusionAA on 4/4 ligands; can co-diffuse ligand geometry.
   - Enzyme scaffolding (AME): beats [[rfdiffusion2]] on 37/41 active sites; 15% vs 4% pass rate on >4 residue islands.
   - Speed: ~10× faster than RFD2.

4. **Experimental validation**:
   - DNA-binding protein targeting CGAGAACATAGTCG: 1/5 designs bound with EC50 = 5.89 ± 2.15 μM.
   - Cysteine hydrolase (Cys-His-Asp triad from Ulp-1): 35/190 designs active; best K_cat/K_m = 3557 M⁻¹s⁻¹.

## Method details

- **Training data**: PDB complexes (protein-protein, protein-small molecule, protein-DNA) through Dec 2024; AF2 distillation structures; scaffolding functional motifs. Hierarchical training procedure to prevent overfitting.
- **Sequence design**: structures are handed to [[proteinmpnn]] or [[ligandmpnn]] for sequence assignment (8 sequences per backbone typical).
- **Evaluation**: [[alphafold3]] predictions used as the primary in silico filter (pAE ≤ 1.5, pTM ≥ 0.8, RMSD < 2.5 Å for binders).

## Figures

- **Fig 1**: diffusion trajectory, model inputs/outputs, architecture diagram, speed comparison.
- **Fig 2**: conditioning modalities — motif scaffolding, DNA/ligand co-diffusion, H-bond conditioning, RASA, center-of-mass, symmetry.
- **Fig 3**: in silico benchmark results across all four design tasks.
- **Fig 4**: experimental results — DNA binder binding curve, cysteine hydrolase Michaelis-Menten kinetics.

## Wiki pages generated

- [[rfdiffusion3]], [[rfdiffusion]], [[rfdiffusion2]], [[alphafold3]], [[david-baker]], [[proteinmpnn]], [[ligandmpnn]]
- [[all-atom-diffusion]], [[classifier-free-guidance]], [[motif-scaffolding]]
