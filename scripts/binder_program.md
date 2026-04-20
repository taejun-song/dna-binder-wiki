# Binder Autoresearch

This is an autonomous experiment loop for optimizing RFdiffusion3 parameters to generate high-quality protein binders.

## Goal

**Get the highest ipTM score** for each target. The ipTM is measured by RoseTTAFold3 (RF3) on the predicted complex. Higher is better. Designs with ipTM >= 0.7 and pTM >= 0.8 pass the quality threshold from the RFD3 paper.

## Targets

### DNA Binder Targets

| Target | DNA Sequence | Template PDB | Contig Pattern |
|--------|-------------|-------------|----------------|
| PNRP1 | TGAGGAGAGGAG | 1BNA.pdb | A1-12,/0,B13-24,/0,LENGTH |
| CAG | CAGCAGCAGCAG | 1BNA.pdb | A1-12,/0,B13-24,/0,LENGTH |
| HSTELO | AGGGTTAGGGTT | 1BNA.pdb | A1-12,/0,B13-24,/0,LENGTH |
| OCT4pt1 | GGTGAAATGA | 1BNA.pdb | A1-10,/0,B13-22,/0,LENGTH |
| OCT4pt2 | GGGCTTGCGA | 1BNA.pdb | A1-10,/0,B13-22,/0,LENGTH |
| NFKB | GGGGATTCCCCC | 1BNA.pdb | A1-12,/0,B13-24,/0,LENGTH |
| HD | GCTTAATTAGCG | 1BNA.pdb | A1-12,/0,B13-24,/0,LENGTH |
| TATA | CGTATAAACG | 1BNA.pdb | A1-10,/0,B13-22,/0,LENGTH |
| Dux4grna2 | CAGGCCGCAGG | 1BNA.pdb | A1-11,/0,B13-23,/0,LENGTH |

### TP53 Tetramerization Inhibitor

| Target | PDB | Description |
|--------|-----|-------------|
| TP53_tet | 8UQR.pdb | p53 tetramerization domain (4 chains A-D, res 324-356) |

**Goal**: Design small binders (<30 aa) that wedge into the dimer-dimer interface to block tetramer formation.

**Interface hotspot residues** (dimer-dimer): L344, L348, A347, L350, M340, F341 (hydrophobic groove) + R337, E343, K351 (salt bridges)

**Contig for TP53**: Fix one dimer (chains A+B), design binder at the dimer-dimer interface:
- `A324-356,B324-356,/0,15-30` — smallest binders targeting interface
- Use `select_hotspots` on interface residues: A344,A348,B344,B348

**Known smallest blocker**: 31 aa peptide (p53[325-355]). Our goal: **beat 31 aa**.

## Pipeline (3 steps)

Each experiment:

1. **RFD3** — generate backbone + initial sequence
   - Binary: `.venv/bin/rfd3`
   - Checkpoint: `~/.foundry/checkpoints/rfd3_latest.ckpt`
2. **ProteinMPNN** — redesign sequence for the generated backbone
   - Binary: `.venv/bin/mpnn`
   - Checkpoint: `~/.foundry/checkpoints/proteinmpnn_v_48_020.pt`
   - Run: `.venv/bin/mpnn --model_type protein_mpnn --structure_path <CIF> --out_directory <DIR> --number_of_batches 4 --checkpoint_path ~/.foundry/checkpoints/proteinmpnn_v_48_020.pt --is_legacy_weights True`
   - This generates FASTA with redesigned sequences. Score the best ProteinMPNN sequence AND the original RFD3 sequence — keep whichever scores higher.
3. **RF3** — score complex (pTM + ipTM)
   - Binary: `.venv/bin/rf3`
   - For DNA targets: score protein + DNA sequence
   - For TP53: score binder + p53 tetramerization domain

4. Record results in `results.tsv`
5. If best_ipTM improved: KEEP config. If not: REVERT.

## What you CAN modify (in rfd3_config.json)

### Per-design JSON fields

- `contig`: residue selection and protein length
- `length`: protein length range (e.g., "100-160")
- `ori_token`: [x, y, z] coordinates controlling binder position
- `is_non_loopy`: true/false — topology constraint
- `select_hbond_donor`: atom-wise H-bond donor conditioning
- `select_hbond_acceptor`: atom-wise H-bond acceptor conditioning
- `select_hotspots`: atom-level or residue-level hotspots
- `select_buried`: RASA buried conditioning
- `select_exposed`: RASA exposed conditioning
- `select_partially_buried`: RASA partially buried conditioning
- `infer_ori_strategy`: "com" or "hotspots"

### Inference sampler overrides (CLI args)

- `inference_sampler.use_classifier_free_guidance`: true/false (CFG)
- `inference_sampler.cfg_scale`: 1.0-3.0 (CFG strength)
- `inference_sampler.step_scale`: 1.0-2.0 (higher = less diverse, more designable)
- `inference_sampler.noise_scale`: 0.8-1.2
- `inference_sampler.num_timesteps`: 50-500 (diffusion steps)
- `inference_sampler.gamma_0`: 0.0-1.0 (stochasticity, 0.0 = ODE)
- `inference_sampler.s_trans`: 0.5-2.0 (translational noise scale)

## What you CANNOT modify

- The target PDB structures
- The RF3 scoring pipeline
- The evaluation harness
- Dependencies or package versions

## Parameter exploration strategy

### Phase 1: Protein length sweep (start short)
Try lengths in this order: 50-70, 60-80, 70-90, 80-100, 80-120, 100-140, 120-160, 140-180
Start from the shortest lengths first. NFKB's best result (ipTM=0.798) came from 80-120 aa — shorter than Baker Lab's 126-150 range.
For TP53: try 15-25, 18-28, 20-30, 25-35 — goal is <31 aa.

### Phase 2: Classifier-free guidance
Enable CFG, sweep cfg_scale: 1.0, 1.5, 2.0, 2.5, 3.0

### Phase 3: Diffusion dynamics
- step_scale: 1.0, 1.25, 1.5, 1.75, 2.0
- noise_scale: 0.8, 0.9, 1.0, 1.1
- gamma_0: 0.0, 0.3, 0.6, 0.9
- num_timesteps: 100, 200, 300

### Phase 4: Orientation and conditioning
- ori_token variations: shift center-of-mass along DNA axis
- is_non_loopy: true vs false
- infer_ori_strategy: "com" vs "hotspots"
- H-bond conditioning on DNA bases
- For TP53: `select_hotspots` on L344, L348, A347, L350

### Phase 5: Combined best parameters
Combine the best settings from phases 1-4

### Phase 6: ProteinMPNN refinement
Take top 10 designs from Phase 5, run ProteinMPNN with 8 sequences each, re-score all with RF3. This often improves ipTM by 0.02-0.05.

## Design principles

1. **Shorter is better.** If two designs have comparable ipTM (within 0.02), prefer the shorter protein. Compact binders are easier to synthesize, more likely to fold correctly, and NFKB's best (98 aa) proves short designs can outperform Baker Lab. Always explore lengths down to 50 aa before moving to longer ranges. For TP53, target <31 aa.

2. **Simpler is better.** A small ipTM improvement from complex conditioning is less valuable than a comparable improvement from a simple parameter change.

3. **ProteinMPNN matters.** Always run ProteinMPNN on the top backbone before final scoring. It can significantly improve sequence quality without changing the structure.

## Results format

Log to `results.tsv` (tab-separated):

```
experiment_id	target	config_change	n_designs	best_iptm	mean_iptm	best_ptm	status
exp001	PNRP1	baseline length=120-140	10	0.607	0.450	0.769	keep
exp002	PNRP1	length=80-120	10	0.580	0.430	0.710	discard
exp003	TP53_tet	length=15-25 hotspots	10	0.450	0.380	0.620	keep
```

## NEVER STOP

Once the experiment loop begins, do NOT pause to ask the human. Run indefinitely until manually interrupted. If you run out of parameter ideas, try combinations of previous near-misses, try more radical changes, try the opposite of what worked.
