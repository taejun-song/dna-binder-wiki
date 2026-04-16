---
type: source-summary
title: "RFD3 Genome Editing Binders Dataset"
created: 2026-04-16
updated: 2026-04-16
sources: []
tags: [dataset, dna-binding, genome-editing, protein-design]
aliases: []
source_file: "../raw/data/RFD3 binders for Genome Editing Assay -BakerLab.csv"
source_kind: csv
---

# RFD3 Genome Editing Binders Dataset

A CSV dataset of 92 [[rfdiffusion3]]-designed DNA-binding protein sequences targeting 9 genomic DNA sequences relevant to genome editing applications.

## Data shape

- **Rows**: 92 (one per designed protein)
- **Columns**: 4
  - `design_name` — full pipeline identifier encoding target sequence, generation parameters, and model/design indices
  - `shorthand_name` — human-readable label (e.g., `PNRP1_design21`, `CAG_specblock_design27`)
  - `amino acid sequence` — full protein sequence (single-letter amino acid code, ~110–145 residues)
  - `on_target_seq` — the DNA target sequence the protein is designed to bind

## Representative row

| design_name | shorthand_name | amino acid sequence | on_target_seq |
|---|---|---|---|
| TGAGGAGAGGAG_3_48_design_4_model_18_dldesign_2_model_dldesign_1_model | PNRP1_design21 | GPEEIRRKKEEAAAILNAWFLA… (127 aa) | TGAGGAGAGGAG |

## Target distribution

| Target | Shorthand | Count |
|---|---|---|
| TGAGGAGAGGAG | PNRP1 | 38 |
| CAGCAGCAGCAG | CAG | 14 |
| AGGGTTAGGGTT | HSTELO | 13 |
| GGGCTTGCGA | OCT4pt2 | 9 |
| GGTGAAATGA | OCT4pt1 | 7 |
| GGGGATTCCCCC | NFKB | 6 |
| GCTTAATTAGCG | HD | 2 |
| CGTATAAACG | TATA | 1 |
| CAGGCCGCAGG | Dux4grna2 | 1 |

## Design naming conventions

- Names without `_specblock_` are initial [[rfdiffusion3]] generations.
- Names containing `_specblock_` are re-scaffolded variants where the major-groove recognition region was fixed and the remaining protein was re-diffused (see [[motif-scaffolding]]).
- The prefix encodes the target DNA sequence; numeric fields encode generation batch, design index, and model/dldesign iteration indices.

## Provenance

Attributed to Baker Lab (Institute for Protein Design, University of Washington). The designs use the DNA-binding protein pipeline described in the [[rfdiffusion3-paper]]. Sequences were likely assigned by [[ligandmpnn]].

## See also

- [[dna-binder-design-targets]] — synthesis page analyzing the 9 targets and their biological relevance
- [[rfdiffusion3]] — the generative model used
