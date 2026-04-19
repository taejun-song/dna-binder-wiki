---
type: synthesis
title: "DNA Binder Generation and Evaluation Report"
created: 2026-04-17
updated: 2026-04-19
sources:
  - "[[rfdiffusion3-paper]]"
  - "[[rfd3-genome-editing-binders]]"
  - "[[autoresearch-karpathy]]"
tags: [dna-binding, protein-design, evaluation, genome-editing, report, autoresearch]
aliases: []
---

# DNA Binder Generation and Evaluation Report

End-to-end report on de novo DNA-binding protein design using [[rfdiffusion3]], comparing our generated binders against Baker Lab reference designs across 9 genome editing targets, culminating in autonomous parameter optimization via [[autoresearch-for-binder-design]].

## 1. Objective

Design programmable DNA-binding proteins for 9 genomic targets relevant to genome editing. Evaluate designs using RoseTTAFold3 (RF3) complex structure prediction with pTM and ipTM as primary metrics, following the evaluation criteria from the [[rfdiffusion3-paper]].

## 2. Evaluation Criteria (from RFD3 paper)

- **pTM >= 0.8** — global fold confidence of the designed protein
- **ipTM >= 0.7** — interface confidence for the protein-DNA complex
- **DNA-aligned RMSD < 5 A** — structural accuracy of the DNA conformation

## 3. Data Sources

### 3.1 Baker Lab Reference Designs

Source: `raw/data/RFD3 binders for Genome Editing Assay -BakerLab.csv`

- **92 pre-designed candidates** across 9 DNA targets
- Generated using [[rfdiffusion3]] with target-specific AF3-predicted DNA conformations
- Includes both initial designs and specblock re-scaffolded variants

### 3.2 Our Generated Designs

Generated using [[rfdiffusion3]] via rc-foundry on an NVIDIA H200 NVL (144GB VRAM).

| Phase | Candidates | Description |
|-------|-----------|-------------|
| Gen2 | 952 | Initial generation, default params, 9 targets |
| Overnight | 2,400+ | Autonomous generation loop, round-robin targets |
| Autoresearch | ~5,000 | 402 experiments, parameter optimization per target |
| **Total** | **~8,400** | **All scored with RF3** |

DNA template: PDB 1BNA (CGCGAATTCGCG, Dickerson dodecamer B-DNA), applied to all targets via contig specification.

## 4. Methodology

### 4.1 Pipeline

```
RFD3 (design generation) → CIF extraction → RF3 (protein-DNA scoring) → TSV logging
```

### 4.2 Phase 1: Baker Lab Evaluation

Scored all 92 Baker Lab candidates with RF3. 9 parallel processes on H200.

### 4.3 Phase 2: Initial Generation (Gen2 + Overnight)

1. Downloaded 1BNA.pdb from RCSB as B-DNA structural template
2. Created RFD3 JSON configs for each target with contigs mapping to 1BNA chains A (residues 1-12) and B (residues 13-24)
3. Ran RFD3 with `n_batches=25-50` per target, multiple waves
4. Scored protein-DNA complexes with RF3
5. Overnight autonomous runner cycled generation -> scoring continuously

### 4.4 Phase 3: Autoresearch Parameter Optimization

Deployed 7-8 autonomous Claude Code agents on the H200 GPU server, each managing a separate DNA target. Agents ran continuously for ~3 days (April 17-19), executing the [[autonomous-experiment-loop]] pattern:

1. Modify RFD3 parameters for a single variable
2. Generate 10-80 designs per experiment
3. Score all outputs with RF3
4. If best_ipTM improved: **keep** the parameter change. If not: **revert**.
5. Move to the next parameter in the sweep

**Parameter axes per target:** protein length, CFG, step scale, noise scale, gamma, topology (is_non_loopy), orientation (com/hotspots), diffusion timesteps, s_trans.

## 5. Autoresearch Agent Session Logs

### 5.1 NFKB Agent (27 experiments, 1,952 scored)

Target: GGGGATTCCCCC | Baker Lab best: 0.753

Found early (exp002) that short proteins (80-120 aa) boost ipTM from 0.575 baseline to **0.798** — surpassing Baker Lab immediately. All 25 subsequent experiments failed to beat this. Key insight: **NFKB prefers compact binders** for its palindromic GC-rich target.

### 5.2 HD Agent (26 experiments, 1,872 scored)

Target: GCTTAATTAGCG | Baker Lab best: 0.803

Found length=100-140 optimal, refined to 110-130 (ipTM **0.733**). However, the overnight run with default parameters had already achieved ipTM **0.772**. The gap to Baker Lab (-0.031 using overnight best) likely requires target-specific DNA geometry.

### 5.3 TATA Agent (8 experiments, 496 scored)

Target: CGTATAAACG | No Baker Lab reference

Clear trend: longer proteins score better. Baseline 0.501 -> 0.620 -> **0.684** at 180-220 aa.

### 5.4 PNRP1 Agent (70 experiments, 5,932 scored)

Target: TGAGGAGAGGAG | Baker Lab best: 0.701

Most experiments — run by 3 overlapping agents. **CFG=1.5 + very long proteins (250-300) + 200 timesteps** pushed ipTM to **0.662**. Gap to Baker Lab: -0.038.

### 5.5 OCT4pt2 Agent (61 experiments, 3,416 scored)

Target: GGGCTTGCGA | Baker Lab best: 0.685

Two agent sessions. AutoRes best: gamma_0=0.3 (ipTM **0.634**). However, overnight default params outperformed at **0.657**. This suggests random diversity matters more than systematic optimization for this target with 1BNA.

### 5.6 OCT4pt1 Agent (27 experiments, 1,856 scored)

Target: GGTGAAATGA | Baker Lab best: 0.646

Already had overnight result ipTM **0.715** (pTM 0.840, passes threshold). AutoRes confirmed: **COM orientation + noise=0.9 + step=1.25** at L=140-180 gives **0.700**. This target shows the clearest evidence that we can surpass Baker Lab with a generic template.

### 5.7 Dux4grna2 Agent (40 experiments, 1,329 scored)

Target: CAGGCCGCAGG | No Baker Lab reference

**Very long proteins (220-260) with COM orientation** gave ipTM **0.641**.

### 5.8 CAG Agent (118 experiments, 4,867 scored)

Target: CAGCAGCAGCAG | Baker Lab best: 0.637

Key discovery: **ODE sampling (gamma=0.0) with noise=0.9** gives **0.648**, edging Baker Lab (+0.011).

### 5.9 HSTELO Agent (25 experiments, 680 scored)

Target: AGGGTTAGGGTT | Baker Lab best: 0.654

AutoRes best: 0.600 (length=140-180). Overnight default params outperformed at **0.639**. Telomeric repeat likely needs non-B-DNA conformations.

## 6. Results

### 6.1 Best ipTM Per Target — All Phases

| Target | Baker Lab | Overnight | AutoRes | Overall Best | Gap vs Baker |
|---------|:---------:|:---------:|:-------:|:------------:|:------------:|
| **NFKB** | 0.753 | 0.645 | **0.798** | **0.798** | **+0.045** |
| **OCT4pt1** | 0.646 | **0.715** | 0.700 | **0.715** | **+0.069** |
| **CAG** | 0.637 | 0.591 | **0.648** | **0.648** | **+0.011** |
| **TATA** | -- | 0.611 | **0.684** | **0.684** | -- |
| **Dux4grna2** | -- | 0.568 | **0.641** | **0.641** | -- |
| HD | **0.803** | **0.772** | 0.733 | 0.772 | -0.031 |
| PNRP1 | **0.701** | 0.607 | **0.662** | 0.662 | -0.038 |
| OCT4pt2 | **0.685** | **0.657** | 0.634 | 0.657 | -0.028 |
| HSTELO | **0.654** | **0.639** | 0.600 | 0.639 | -0.015 |

**We beat Baker Lab on 3 of 7 compared targets** (NFKB, OCT4pt1, CAG). For HD, OCT4pt2, and HSTELO, overnight generation with default parameters outperformed systematic autoresearch — suggesting stochastic diversity can be more valuable than parameter optimization when using a generic DNA template.

### 6.2 Candidates Passing ipTM >= 0.7

| # | Target | Design | pTM | ipTM | Source |
|---|--------|--------|-----|------|--------|
| 1 | NFKB | config_design_3_model_3 | 0.724 | **0.798** | **Ours (AutoRes)** |
| 2 | HD | specblock_design82 | 0.895 | **0.803** | Baker Lab |
| 3 | HD | specblock_design94 | 0.852 | **0.790** | Baker Lab |
| 4 | HD | HD_config_HD_19_model_3 | 0.675 | **0.772** | **Ours (Overnight)** |
| 5 | NFKB | specblock_design66 | 0.862 | **0.753** | Baker Lab |
| 6 | NFKB | specblock_design82 | 0.880 | **0.753** | Baker Lab |
| 7 | NFKB | specblock_design65 | 0.867 | **0.718** | Baker Lab |
| 8 | OCT4pt1 | OCT4pt1_18_model_0 | 0.840 | **0.715** | **Ours (Overnight)** |
| 9 | PNRP1 | specblock_design39 | 0.899 | **0.701** | Baker Lab |
| 10 | OCT4pt1 | config_design_6_model_0 | 0.908 | **0.700** | **Ours (AutoRes)** |

**10 candidates pass ipTM >= 0.7**: 6 Baker Lab, 4 ours.

### 6.3 Production Statistics

| Metric | Baker Lab | Ours (all phases) |
|--------|----------|-------------------|
| Total candidates | 92 | ~8,400 |
| RF3 scored | 92 | ~24,400 |
| Autoresearch experiments | -- | 402 |
| Passing ipTM >= 0.7 | 6 | 4 |
| Targets beating Baker Lab | -- | 3 / 7 |

## 7. Top Candidate Sequences

### NFKB — AutoRes Best (ipTM=0.798, pTM=0.724, 98 aa)

Params: length=80-120

```
ARVRVVRTPAQIAALLAAADQYASQGLSAAELNDLALRVGLTQAQVENWFANRQRKVNGR
PSPTAAERANRKLAKNKNAAENAEALKASLNLLIDANM
```

### HD — Overnight Best (ipTM=0.772, pTM=0.675, 131 aa)

```
AAKPRTVWTALQKQTLEEWLNQHKDNPYPTKAERAKLAEDLNVTVTQVKNWFANRRQKLQ
AQDMGITYAEYLKKRSLCSADKNANTPIAQLEALIQKKEAQLAAAIALGAPESTILALENTT
IDNLKKNLNK
```

### OCT4pt1 — Overnight Best (ipTM=0.715, pTM=0.840, 125 aa) — PASSES FULL THRESHOLD

```
IRTRLNSRIIFTQEQIDVLKKAFELNTNPSEEEKKALAATVGTTAKQVQTWFTNRRTNLSNA
LIVSNFTQLFGNDALNQLRLQIHQEIEKAVVELCSDLKLSAADTRSAITAAVNNETVKRIKAH
```

### CAG — AutoRes Best (ipTM=0.648, pTM=0.713, 189 aa)

Params: noise=0.9 gamma=0.0

```
GAAAAAAAAAALLAAGNAALKAGSYAAAIAAYNQAIALNPTNAAAYLNLGNAYSKLGNTAAAI
AAYNKALALNPNNTTAQINLAKAQGDAAAAAAIAAANAAANPAAALTQAGQTAAAIAALYQAA
AATGSPAAQAAALNNLGAIYQAQGQLAAAIAAAYQAALALAAPTSPALAAALAANLAATQAALAA
```

### TATA — AutoRes Best (ipTM=0.684, pTM=0.865, 196 aa)

```
SHLAQAAAAKKKGDFDTAIALLNQVLLIAPAAKQANAYLALATALTAQGNLDKAQAALKKALAI
QPSNTSAKLSLAAVLLKQGDVDKALALYRQLAAQGSTTARIKLANHFAQQGQLDAAVATLEAA
LADTAQNAPTSGARVALLLNLAGLYKKAARLDDAVQAYQQAAQVAQLINNAAAAASQAENNAAN
LEKAAT
```

### Dux4grna2 — AutoRes Best (ipTM=0.641, pTM=0.833, 253 aa)

```
GAQQALNNKALTLLNQKQYADAIQVLDKMEELGFTPDLSTYLIRGDALINLGQVNAAIADYH
SAIEKNPSLVDSATYKNLGNAYKKAGEYDNAIAQFNKAIELNPTNLTAYNNLANTYQDMGKND
LAIAAYDKAISLFPNSASAASATTNLGRVLASKGDVDAAVKAYENAISTAQKNKANVLAAISFQ
NLAAVFKAQGKSADAAAQLVASAAARLAANANSAQAYADLAEAFELLGKSADAATMQAKALTLA
```

### PNRP1 — AutoRes Best (ipTM=0.662, pTM=0.825, 272 aa)

```
AAADSIAKGKQLIKAGQDAQAQALYEAVLKQFPDTAEAATAALNLGNLYMKQKKYDLAIQHYK
KAAKLLPAAAYNNIGNAYLAQGLIDNAIAAYNKALELNPQYAAAYNNKGVAYKAKGKDDEAIAD
FNRALALNPNYNAARKNLGILQLKLNIPEGALLLNIANTYNSALNLLNKANAAALQAGDSQQARQ
LLEAALASLDSALAQTNDQDVALLSAKLSALENLAQIAEPSEFPSLAQRLVAVAQQLLAVGNLGA
ANRAQTAAQACTAAAT
```

### OCT4pt2 — Overnight Best (ipTM=0.657, pTM=0.807, 124 aa)

```
DQIASLQKRLASSKPVVVKPLTPAQAYERLKAALLAATEPTLLKRAALLGTTVETLRALAAPDN
TDLATAQSKYTQLATICAKKNAVQRKIRVKKELVSAQELAAEIRNASVKALETADELAPNV
```

### HSTELO — Overnight Best (ipTM=0.639, pTM=0.656, 133 aa)

```
TTITVTKAELIALVEAFCADVNISFETLRTLIASKASKSAFSIADLVKAFEERH
PAIKLIVNQANQHKAQNRVTFPQSAVDMLDALLVQKDYKPPTKAERTALAKRT
SLTPAQIATWAANRRSNLAKKKAKNK
```

## 8. Sequence Feature Analysis

### Motif Convergence

Several of our designs independently discover homeodomain-like motifs:

- **NFKB autoresearch**: `VENWFA` — variant of the WF(Q/A) recognition motif
- **HD overnight**: `WFANRRQK` — classic homeodomain recognition helix
- **HD autoresearch**: `WFANRRAS` — same motif, different scaffold
- **OCT4pt1 overnight**: `QVQTWF` — another WF variant

This convergence suggests RFD3 naturally discovers homeodomain-like DNA recognition even from a generic template.

### Key Autoresearch Discoveries

| Discovery | Target(s) | Insight |
|-----------|-----------|---------|
| Short proteins (80-120) | NFKB | Compact binders for palindromic GC-rich targets |
| Very long proteins (180-300) | TATA, Dux4grna2, PNRP1 | AT-rich/repeat targets need extensive scaffold |
| ODE sampling (gamma=0.0) | CAG | Deterministic sampling for repeat sequences |
| COM orientation | OCT4pt1, Dux4grna2 | Center-of-mass placement improves binding geometry |
| Default params sometimes win | HD, OCT4pt2, HSTELO | Stochastic diversity > systematic optimization for some targets |

## 9. Recommendations

### 9.1 Immediate: Target-Specific DNA Structures

Generate proper DNA structures for each target using AF3 to close remaining gaps on HD (-0.031), OCT4pt2 (-0.028), HSTELO (-0.015), PNRP1 (-0.038).

### 9.2 Short-term: Specblock Re-scaffolding

Apply specblock to our top designs — fix the recognition interface and regenerate the scaffold.

### 9.3 Experimental Validation

1. **NFKB autoresearch best** (ipTM 0.798) — highest-confidence novel design
2. **OCT4pt1 overnight** (ipTM 0.715, pTM 0.840) — passes full threshold
3. **HD overnight** (ipTM 0.772) — convergent WF motif
4. **CAG autoresearch** (ipTM 0.648) — novel ODE-sampling finding

## 10. Compute Resources

- **GPU**: NVIDIA H200 NVL (144GB VRAM)
- **Duration**: 5 days (April 15-19, 2026)
- **Total structures generated**: ~8,400
- **Total complexes scored**: ~24,400
- **Autoresearch**: 402 experiments, 72 hours, 7-8 concurrent agents

## See also

- [[rfdiffusion3]] — the generative model
- [[dna-binder-design-targets]] — the 9 genomic targets
- [[rfd3-genome-editing-binders]] — Baker Lab reference dataset
- [[autoresearch-for-binder-design]] — parameter optimization strategy
- [[autonomous-experiment-loop]] — the autoresearch methodology
