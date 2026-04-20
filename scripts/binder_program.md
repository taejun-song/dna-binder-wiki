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

### Optuna-guided optimization (preferred)

Use the Optuna suggestion script to choose parameters. It uses Bayesian optimization (TPE) to model which parameter combinations produce high ipTM, and suggests the most promising next experiment.

```bash
# Get next suggested params for DNA target:
.venv/bin/python scripts/optuna_suggest.py --target TARGET --results analysis_output/autoresearch/TARGET_agent2.tsv

# For TP53:
.venv/bin/python scripts/optuna_suggest.py --target TP53_tet --results analysis_output/tp53/tp53_results.tsv --tp53
```

The script outputs JSON with suggested `length`, `sampler_overrides`, and optionally `infer_ori_strategy`. Use these for your next experiment. After scoring, log the result to the TSV, then call the script again for the next suggestion.

**Why Optuna beats grid search**: it learns from previous experiments to suggest parameter combinations (not one axis at a time). After ~10 trials it focuses on the most promising regions of parameter space.

### Fallback: manual exploration (if Optuna is unavailable)

Phase 1: Length sweep (start short) — 50-70, 60-80, 70-90, 80-100, 80-120, 100-140, 120-160, 140-180
Phase 2: CFG — cfg_scale: 1.0, 1.5, 2.0, 2.5, 3.0
Phase 3: Dynamics — step_scale, noise_scale, gamma_0, num_timesteps
Phase 4: Orientation — infer_ori_strategy: "com" vs "hotspots", is_non_loopy
Phase 5: Combined best parameters
For TP53: lengths 12-30, select_hotspots on L344, L348, A347, L350

### ProteinMPNN refinement (always do this)

After every experiment, run ProteinMPNN on the top backbone to get redesigned sequences. Score both the RFD3 sequence and ProteinMPNN sequences with RF3 — keep the best. This often improves ipTM by 0.02-0.05.

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
