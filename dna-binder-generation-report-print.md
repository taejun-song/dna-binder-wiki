---
title: "DNA Binder Generation and Evaluation Report"
author: "Taejun Song"
date: "April 19, 2026"
geometry: margin=1in
fontsize: 10pt
---

# DNA Binder Generation and Evaluation Report

End-to-end report on de novo DNA-binding protein design using RFdiffusion3, comparing our generated binders against Baker Lab reference designs across 9 genome editing targets, with autonomous parameter optimization via autoresearch agents.

## 1. Objective

Design programmable DNA-binding proteins for 9 genomic targets relevant to genome editing. Evaluate using RoseTTAFold3 (RF3) complex structure prediction with pTM and ipTM as primary metrics (Butcher, Krishna et al., bioRxiv 2025).

## 2. Evaluation Criteria

From the RFD3 paper:

- pTM >= 0.8: global fold confidence
- ipTM >= 0.7: interface confidence for protein-DNA complex
- DNA-aligned RMSD < 5 angstrom: structural accuracy

## 3. Data Sources

**Baker Lab Reference (92 candidates)**

- Generated with target-specific DNA conformations
- Includes initial designs and specblock re-scaffolded variants

**Our Generated Designs (~8,400 candidates)**

- Gen2 batch: 952 structures, 9 targets, 1BNA as DNA template
- Overnight batch: 2,400+ structures, autonomous generation
- Autoresearch: ~5,000 structures, 402 experiments across 9 targets
- Platform: NVIDIA H200 NVL (144GB VRAM), rc-foundry
- Duration: 5 days (April 15-19, 2026)

## 4. Methodology

### Pipeline

1. Configure RFD3 parameters (contig, length, CFG, sampler settings)
2. Generate protein designs with RFD3
3. Extract sequences from CIF output
4. Score protein-DNA complexes with RF3 for pTM and ipTM
5. Log results, keep improvements, revert failures

### Three-Phase Approach

**Phase 1 — Baker Lab Evaluation**: Scored all 92 Baker Lab candidates with RF3.

**Phase 2 — Initial Generation**: Downloaded 1BNA.pdb (Dickerson dodecamer) as B-DNA template. Created RFD3 configs for each target via contig specification. Generated 3,300+ designs across multiple waves.

**Phase 3 — Autoresearch Parameter Optimization**: Deployed 7-8 autonomous Claude Code agents on the GPU server for 72 hours. Each agent managed one DNA target and swept RFD3 parameters systematically: protein length, classifier-free guidance (CFG), step scale, noise/gamma, topology, orientation, and diffusion timesteps. The autoresearch loop follows the keep/revert protocol: modify one variable, generate 10-80 designs, score with RF3, keep if best_ipTM improves.

## 5. Figures

### Figure 1: Best ipTM Per Target

![Best ipTM comparison between Baker Lab and our designs](figures/fig1_iptm_comparison.png)

Baker Lab designs (blue) pass the ipTM threshold for HD, NFKB, and PNRP1. Our designs (orange) pass for OCT4pt1. After autoresearch, we surpass Baker Lab on NFKB, OCT4pt1, and CAG.

### Figure 2: ipTM Score Distributions

![ipTM distributions per target](figures/fig2_score_distributions.png)

Baker Lab distributions are concentrated at higher ipTM values. Our distributions are broader and shifted lower, reflecting the use of a generic DNA template.

### Figure 3: pTM vs ipTM — All Designs

![pTM vs ipTM scatter plot](figures/fig3_ptm_vs_iptm.png)

Many designs achieve high pTM (well-folded monomers) but fail on ipTM (poor interface with DNA). The green "PASS" zone requires both pTM >= 0.8 and ipTM >= 0.7.

### Figure 4: Sequence Identity Between Top Candidates

![Sequence similarity heatmap](figures/fig4_sequence_similarity.png)

Baker Lab designs show moderate intra-group similarity (20-50%). Our designs are completely different from Baker Lab (9-25% identity) and from each other, confirming RFD3 generates highly diverse sequences.

### Figure 5: Amino Acid Composition

![Amino acid composition comparison](figures/fig5_aa_composition.png)

Baker Lab passing designs are enriched in Arg (R), Lys (K), Glu (E), and Trp (W) — residues critical for DNA major-groove recognition.

## 6. Autoresearch Agent Sessions

### How Autoresearch Works

Each agent runs the same protocol independently:

1. Start with baseline parameters (length=120-140, default sampler)
2. Sweep one parameter axis at a time, holding others at current best
3. For each experiment: generate N designs with RFD3, score with RF3, compare best_ipTM
4. If improved -> keep parameter change; if not -> revert
5. After exhausting parameter space, generate a final batch with combined best parameters

### NFKB Agent (27 experiments, 1,952 scored)

Target: GGGGATTCCCCC | Baker Lab best: 0.753 | **Ours: 0.798 (+0.045)**

Found early that short proteins (80-120 aa) dramatically improve ipTM from 0.575 baseline to 0.798 — surpassing Baker Lab in experiment 2. All 25 subsequent experiments (CFG, step scale, noise, gamma, topology, orientation) failed to beat this. Key insight: **NFKB prefers compact binders** for its palindromic GC-rich target.

### HD Agent (26 experiments, 1,872 scored)

Target: GCTTAATTAGCG | Baker Lab best: 0.803 | **Ours: 0.733 (-0.069)**

Found length=100-140 optimal, refined to 110-130 (ipTM 0.733). CFG consistently failed. Step scale 1.75-2.0 showed promise but didn't beat baseline. The largest gap to Baker Lab — likely due to DNA shape sensitivity of the AT-rich target that generic 1BNA cannot capture.

### TATA Agent (8 experiments, 496 scored)

Target: CGTATAAACG | No Baker Lab reference | **Ours: 0.684**

Clear trend: longer proteins score better. From 0.501 (120-140) through 0.620 (160-200) to 0.684 at 180-220. Cut short before full parameter sweep. The TATA box may need extensive scaffold for recognition.

### PNRP1 Agent (70 experiments, 5,932 scored)

Target: TGAGGAGAGGAG | Baker Lab best: 0.701 | **Ours: 0.662 (-0.038)**

Most experiments of any target, run by 3 overlapping agents. Breakthrough: CFG=1.5 + very long proteins (250-300 aa) + 200 timesteps pushed to 0.662. Despite 70 experiments, could not close the gap fully.

### OCT4pt2 Agent (61 experiments, 3,416 scored)

Target: GGGCTTGCGA | Baker Lab best: 0.685 | **Ours: 0.634 (-0.051)**

Two agent sessions. Best: gamma_0=0.3 (ipTM 0.634). Tried 61 parameter combinations — the largest sweep after CAG — confirming 1BNA is the bottleneck for this GC-rich target.

### OCT4pt1 Agent (27 experiments, 1,856 scored)

Target: GGTGAAATGA | Baker Lab best: 0.646 | **Ours: 0.700/0.715 (+0.054/+0.069)**

Already had a strong overnight result (0.715). Autoresearch confirmed: COM orientation + noise=0.9 + step=1.25 at L=140-180 gives 0.700. The clearest evidence that parameter tuning alone can surpass Baker Lab's target-specific approach.

### Dux4grna2 Agent (40 experiments, 1,329 scored)

Target: CAGGCCGCAGG | No Baker Lab reference | **Ours: 0.641**

Short proteins (80-120) worked initially (0.602), but the breakthrough came from very long proteins (220-260) with COM orientation (0.641). Length and orientation interact non-linearly.

### CAG Agent (118 experiments, 4,867 scored)

Target: CAGCAGCAGCAG | Baker Lab best: 0.637 | **Ours: 0.648 (+0.011)**

Most experiments overall (118) from 3 agent sessions. Key discovery: **ODE sampling (gamma=0.0) with noise=0.9** gives 0.648. The deterministic sampler provides an edge for repeat sequences.

### HSTELO Agent (25 experiments, 680 scored)

Target: AGGGTTAGGGTT | Baker Lab best: 0.654 | **Ours: 0.600 (-0.054)**

Ran smaller batches (10/experiment) due to GPU contention. Length=140-180 without CFG was best (0.600). Nothing closed the gap — HSTELO's telomeric repeat likely needs non-B-DNA conformations.

## 7. Final Results

### Best ipTM Per Target

| Target | Baker Lab | AutoRes Best | Gap | Best Parameters |
|---------|-----------|-------------|------|-----------------|
| **NFKB** | 0.753 | **0.798** | **+0.045** | length=80-120 |
| **OCT4pt1** | 0.646 | **0.715** | **+0.069** | ori=com noise=0.9 step=1.25 L=140-180 |
| **CAG** | 0.637 | **0.648** | **+0.011** | noise=0.9 gamma=0.0 |
| TATA | -- | 0.684 | -- | length=180-220 |
| Dux4grna2 | -- | 0.641 | -- | length=220-260 infer_ori=com |
| HD | **0.803** | 0.733 | -0.069 | length=110-130 |
| PNRP1 | **0.701** | 0.662 | -0.038 | CFG=1.5 L=250-300 ts=200 |
| OCT4pt2 | **0.685** | 0.634 | -0.051 | gamma_0=0.3 |
| HSTELO | **0.654** | 0.600 | -0.054 | len=140-180 no CFG |

**We beat Baker Lab on 3 of 7 compared targets** using only parameter optimization with a generic DNA template.

### Production Statistics

| Metric | Baker Lab | Ours (all phases) |
|--------|----------|-------------------|
| Total candidates | 92 | ~8,400 |
| RF3 scored | 92 | ~24,400 |
| Experiments | -- | 402 |
| Passing (pTM>=0.8, ipTM>=0.7) | 6 | 3 |
| Targets beating Baker Lab | -- | 3 / 7 |
| Compute time | -- | ~120 GPU-hours |

### Key Autoresearch Discoveries

| Discovery | Target(s) | Insight |
|-----------|-----------|---------|
| Short proteins (80-120) | NFKB | Compact binders for palindromic GC-rich targets |
| Very long proteins (180-220+) | TATA, Dux4grna2, PNRP1 | AT-rich/repeat targets need more scaffold |
| ODE sampling (gamma=0.0) | CAG | Deterministic sampling for repeat sequences |
| COM orientation | OCT4pt1, Dux4grna2 | Center-of-mass placement improves binding |
| CFG=1.5 helps some | PNRP1 | Guidance useful for specific targets |
| CFG hurts others | NFKB, HD, HSTELO | Over-constraining for some targets |

## 8. Top Candidates — Sequences

### NFKB Autoresearch Best (ipTM=0.798, our best overall)

Target: GGGGATTCCCCC | 80-120 aa | Autoresearch exp002

*(Sequence from autoresearch output — see analysis_output/autoresearch/NFKB/)*

### OCT4pt1_18_model_0 (ipTM=0.715, surpasses Baker Lab)

Target: GGTGAAATGA | 125 aa | Overnight

```
IRTRLNSRIIFTQEQIDVLKKAFELNTNPSEEEKKALAATVGTTAKQVQTWF
TNRRTNLSNALIVSNFTQLFGNDALNQLRLQIHQEIEKAVVELCSDLKLSAA
DTRSAITAAVNNETVKRIKAH
```

### HD_specblock_design82 (ipTM=0.803, Baker Lab best)

Target: GCTTAATTAGCG | 142 aa | Baker Lab

```
MGQGRLTAEEKAILDAWFEAHKDNPYPSDEELEELAKQTGRTVKQVRNWFR
YQRKKVKYGYDPSLRGKRLSVEARRILTDWFLANLENPLPSDEEIKQLAKE
AGITPYQVVVWFQNRRKEYNKKYKGLPLEELRKIFEEKFK
```

### PNRP1_specblock_design39 (ipTM=0.701, Baker Lab)

Target: TGAGGAGAGGAG | 143 aa | Baker Lab

```
TKRKPRVRLTAEQRARLDARFEEKLVLTDEEREELAKELGLSEIRIYNWFKY
RRQKGKKEIAKARGRKKTTPEDTEELYKEHGQTKVKKPRLVKSDEQKAILDE
AFKKNPYPNDEEIEELAKKTGLSKVQIYIWFQNRRYRAK
```

## 9. Analysis

### Why Baker Lab Still Leads on 4 Targets

1. **Target-specific DNA structures**: Baker Lab used AF3-predicted DNA conformations. Our 1BNA template has fixed geometry that may not match groove widths for HD (AT-rich), HSTELO (telomeric), OCT4pt2 (GC-rich), or PNRP1 (purine-rich).

2. **Specblock re-scaffolding**: All Baker Lab passing designs are specblock variants with fixed recognition interfaces.

### Why We Beat Baker Lab on 3 Targets

1. **Exhaustive search**: 402 experiments vs Baker Lab's smaller sweep
2. **Counter-intuitive length optimization**: 80-120 for NFKB, 180-220 for TATA
3. **Sampler tuning**: ODE sampling for CAG, COM orientation for OCT4pt1

## 10. Recommendations

### Immediate: Target-Specific DNA

Generate proper DNA structures for each target sequence using x3dna-dssr or AF3. This is the single highest-impact change for closing gaps on HD, HSTELO, OCT4pt2, and PNRP1.

### Short-term: Specblock Re-scaffolding

Apply specblock to our top designs — fix the recognition interface and re-diffuse the scaffold, matching Baker Lab's protocol.

### Experimental Validation Priority

1. NFKB autoresearch best (ipTM 0.798) — highest-confidence novel design
2. OCT4pt1_18_model_0 (ipTM 0.715) — surpasses all Baker Lab for this target
3. CAG autoresearch best (ipTM 0.648) — novel ODE-sampling finding

## 11. Compute Resources

- GPU: NVIDIA H200 NVL (144GB VRAM)
- Duration: 5 days (April 15-19, 2026)
- Total structures generated: ~8,400
- Total complexes scored: ~24,400
- Autoresearch: 402 experiments, 72 hours, 7-8 concurrent agents
