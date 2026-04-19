# DNA Binder Autoresearch

This is an autonomous experiment loop for optimizing RFdiffusion3 parameters to generate high-quality DNA-binding proteins.

## Goal

**Get the highest ipTM score** for each DNA target. The ipTM is measured by RoseTTAFold3 (RF3) on the predicted protein-DNA complex. Higher is better. Designs with ipTM >= 0.7 and pTM >= 0.8 pass the quality threshold from the RFD3 paper.

## Setup

Each experiment:

1. Modify `rfd3_config.json` — the only file the agent edits
2. Run RFD3 to generate designs (~1-2 min per batch on H200)
3. Extract protein sequences from CIF output
4. Score with RF3 for pTM + ipTM (~30s per complex)
5. Record results in `results.tsv`
6. If best_ipTM improved: KEEP config. If not: REVERT.

## What you CAN modify (in rfd3_config.json)

### Per-design JSON fields

- `contig`: DNA residue selection and protein length (e.g., "A1-12,/0,B13-24,/0,100-160")
- `length`: protein length range (e.g., "100-160")
- `ori_token`: [x, y, z] coordinates controlling binder position relative to DNA
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

- The DNA template PDB (1BNA.pdb)
- The RF3 scoring pipeline
- The evaluation harness
- Dependencies or package versions

## Parameter exploration strategy

### Phase 1: Protein length sweep
Try lengths: 50-80, 60-90, 70-100, 80-120, 100-140, 120-160, 140-180, 160-200

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

### Phase 5: Combined best parameters
Combine the best settings from phases 1-4

## Simplicity criterion

All else being equal, simpler is better. A small ipTM improvement from complex conditioning is less valuable than a comparable improvement from a simple parameter change.

## Results format

Log to `results.tsv` (tab-separated):

```
experiment_id	target	config_change	n_designs	best_iptm	mean_iptm	best_ptm	status
exp001	PNRP1	baseline length=120-140	10	0.607	0.450	0.769	keep
exp002	PNRP1	length=80-120	10	0.580	0.430	0.710	discard
exp003	PNRP1	length=140-180	10	0.650	0.480	0.820	keep
```

## NEVER STOP

Once the experiment loop begins, do NOT pause to ask the human. Run indefinitely until manually interrupted. If you run out of parameter ideas, try combinations of previous near-misses, try more radical changes, try the opposite of what worked.
