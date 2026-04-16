---
type: synthesis
title: "Autoresearch for DNA Binder Design"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[autoresearch-karpathy]]"
  - "[[rfdiffusion3-paper]]"
  - "[[rfd3-genome-editing-binders]]"
tags: [methodology, protein-design, dna-binding, optimization, ai-agent]
aliases: []
---

# Autoresearch for DNA Binder Design

Applying the [[autonomous-experiment-loop]] pattern from [[autoresearch]] to [[rfdiffusion3]] DNA binder parameter optimization, using ipTM from RoseTTAFold3 as the optimization metric.

## Motivation

RFD3 has many configurable parameters that affect binder quality: protein length, contig specification, orientation tokens, hydrogen-bond donor/acceptor constraints, RASA labels, and [[classifier-free-guidance]] strength. Manual exploration of this parameter space is slow. The autoresearch pattern automates this: an AI agent proposes parameter changes, RFD3 generates binders, RF3 scores them, and the agent keeps or reverts based on ipTM.

## Mapping to protein design

| Autoresearch (LLM) | Binder design (RFD3) |
|---|---|
| `train.py` (agent modifies) | RFD3 JSON config (agent modifies) |
| `program.md` (human writes) | `binder_program.md` — target DNA, design objectives, parameter bounds |
| 5-minute training run | RFD3 generation (~1 min) + RF3 scoring (~30s per design) |
| val_bpb (lower is better) | ipTM (higher is better) — protein-DNA complex confidence |
| Keep/revert decision | Keep parameter set if best ipTM across batch exceeds previous best |

## Proposed pipeline

### Fixed components (not modified by agent)

- Target DNA structure PDB
- RF3 scoring pipeline
- Evaluation harness (parse ipTM from RF3 output)

### Agent-modifiable parameters

| Parameter | Type | Range | Effect |
|---|---|---|---|
| `protein_length` | range | 80–200 | Binder size |
| `contig` | string | DNA residue selection | Which DNA residues to target |
| `ori_token` | list[int] | varies | Orientation of binder relative to DNA |
| `num_designs` | int | 5–50 | Batch size per experiment |
| `is_non_loopy` | bool | true/false | Topology constraint |
| H-bond constraints | atom selection | varies | Specify donor/acceptor atoms |
| RASA labels | per-atom | buried/exposed | Control burial of interface atoms |

### Experiment loop

```
repeat:
    1. Agent reads binder_program.md + previous results
    2. Agent modifies rfd3_config.json (one parameter change)
    3. RFD3 generates N binders (~1 min on H200)
    4. ProteinMPNN assigns sequences
    5. RF3 scores protein-DNA complexes → ipTM
    6. Record: parameter_change, best_ipTM, mean_ipTM, num_passing
    7. If best_ipTM > previous_best: KEEP config
       Else: REVERT to previous config
    8. Log experiment to results.md
```

### Time budget

On an NVIDIA H200:
- RFD3 generation: ~1 min for 10 designs
- ProteinMPNN: ~10s for 10 sequences
- RF3 scoring: ~30s per complex × 10 = ~5 min
- **Total per experiment: ~7 min → ~8 experiments/hour → ~65 overnight**

### Metric: ipTM

ipTM (interface predicted TM-score) from RF3 measures confidence in the protein-DNA interface:
- ipTM > 0.8: high-confidence complex
- ipTM 0.6–0.8: moderate confidence
- ipTM < 0.6: unlikely to bind

The agent optimizes for max(ipTM) across the batch, with secondary metrics:
- Fraction of designs with ipTM > 0.7
- Mean pTM (global fold quality)
- Sequence diversity of passing designs

## Expected outcomes

1. **Parameter sensitivity map**: which RFD3 parameters most affect ipTM for each DNA target
2. **Optimized configs per target**: best parameter sets for PNRP1, CAG, HSTELO, etc.
3. **Higher-quality binders**: designs with ipTM > 0.8 that were not found with default parameters
4. **Emergent strategies**: the agent may discover non-obvious parameter combinations

## Risks and limitations

- **Metric gaming**: ipTM is a predicted score, not experimental binding. High-ipTM designs may not bind in vitro.
- **Local optima**: hill-climbing may miss globally optimal parameter regions. Could be mitigated with periodic random restarts.
- **Compute cost**: each experiment uses GPU for both RFD3 and RF3. ~65 experiments overnight on one H200.
- **Parameter interactions**: single-parameter changes may miss synergistic multi-parameter optima.

## See also

- [[autoresearch]] — the original framework
- [[autonomous-experiment-loop]] — the general methodology
- [[rfdiffusion3]] — the generative model being optimized
- [[dna-binder-design-targets]] — the DNA targets for optimization
