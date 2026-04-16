---
type: entity
title: "RFdiffusion3"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [model, diffusion, protein-design, baker-lab]
aliases: [RFD3]
---

# RFdiffusion3

An all-atom diffusion model for de novo protein design that generates backbone and sidechain coordinates simultaneously in the context of arbitrary non-protein atoms.

## Overview

RFdiffusion3 (RFD3) extends the RFdiffusion family from residue-level to [[all-atom-diffusion]]. It can design protein binders, DNA-binding proteins, small-molecule binders, enzymes, and symmetric assemblies — all within a single model. It was developed at the Institute for Protein Design (University of Washington) by [[david-baker]]'s group and collaborators.

## Architecture

- **Base**: transformer-based U-Net adapted from the [[alphafold3]] diffusion module.
- **Atom representation**: 14 atoms per residue (4 backbone + 10 sidechain slots with virtual atom padding).
- **Three modules**: (i) downsampling encoder for atomic/residue features, (ii) sparse token transformer (18 blocks), (iii) upsampling decoder with atom transformer blocks (3+3).
- **Information flow**: sparse attention within residues at the atom level; cross-attention between atom and token tracks for up-pool / down-pool.
- **Parameters**: ~168M (vs ~350M for AF3).
- **Key omission**: triangle attention and triangle multiplicative updates are removed for efficiency.
- **Pairformer**: shrunk from 48 layers (AF3) to 2 layers.
- **Training data**: PDB complexes (protein-protein, protein-small molecule, protein-DNA) through December 2024, plus AF2 distillation structures and scaffolding functional motifs.

## Conditioning capabilities

| Conditioning type | Description |
|---|---|
| Binding target | Fixed coordinates of the target protein / DNA / ligand |
| Atom-level hotspots | Specify which atoms should form the interface |
| H-bond donor/acceptor | Label specific atoms as donors or acceptors |
| Solvent accessibility (RASA) | Per-atom burial/exposure labels |
| Center-of-mass | Position the designed protein relative to the target |
| Symmetric noise | Generate Cn or Dn symmetric assemblies |
| Functional motifs | Fix motif atom coordinates inside the noise cloud |

All conditioning types benefit from [[classifier-free-guidance]].

## Performance (in silico)

- **Protein binders**: outperforms [[rfdiffusion]] on 4/5 therapeutically relevant targets (PD-L1, IL-2Rα, IL-7Rα, Tie2, InsulinR); ~8.2 vs 1.4 unique successful backbone clusters.
- **DNA binders**: 8.67% monomeric / 6.67% dimeric pass rate (<5 A DNA-aligned RMSD); can jointly predict DNA shape.
- **Small-molecule binders**: outperforms RFdiffusionAA on all 4 tested ligands (FAD, SAM, IAI, OQO); can co-diffuse ligand conformation.
- **Enzyme design (AME)**: beats [[rfdiffusion2]] on 37/41 active sites; handles up to 7 residue islands.
- **Speed**: ~10× faster than RFD2 at typical lengths (NVIDIA A6000 GPUs).
- **Unconditional generation**: 98% of designs (length 100–200) have at least one sequence predicted by AF3 to fold within 1.5 A RMSD.

## Experimental validation

- **DNA-binding protein**: designed against target sequence CGAGAACATAGTCG; 1/5 designs bound with EC50 = 5.89 ± 2.15 μM (yeast surface display).
- **Cysteine hydrolase**: Cys-His-Asp catalytic triad scaffolded using Ulp-1 crystal structure; 35/190 designs showed multi-turnover activity; best K_cat/K_m = 3557 M⁻¹s⁻¹, exceeding prior RFD2 designs.

## Sequence design

RFD3 generates structures, not sequences. Sequences are assigned downstream using [[proteinmpnn]] (protein-only contexts) or [[ligandmpnn]] (contexts with non-protein atoms).

## Relation to prior models

- [[rfdiffusion]] (RFD1): residue-level backbone-only diffusion. RFD3 subsumes its capabilities with higher diversity.
- [[rfdiffusion2]] (RFD2): hybrid residue-atom for enzyme active sites. RFD3 replaces the hybrid representation with unified all-atom diffusion.
- [[alphafold3]]: structure prediction model whose diffusion module architecture RFD3 adapts and simplifies for design.

## See also

- [[motif-scaffolding]] — a key application enabled by RFD3's atom-level precision
- [[all-atom-diffusion]] — the generative paradigm RFD3 implements
