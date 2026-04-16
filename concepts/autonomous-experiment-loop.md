---
type: concept
title: "Autonomous Experiment Loop"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[autoresearch-karpathy]]"
tags: [methodology, ai-agent, optimization, automation]
aliases: [autoresearch loop, agent-driven experimentation]
---

# Autonomous Experiment Loop

A methodology where an AI agent iteratively modifies experimental parameters, runs an experiment, evaluates a single metric, and keeps or reverts the change — repeating autonomously without human intervention.

## Core pattern

1. **Read objectives** — agent consumes a human-written instruction file (e.g., `program.md`)
2. **Modify parameters** — agent edits the experiment configuration
3. **Run experiment** — fixed time/compute budget per run
4. **Evaluate** — compare metric against previous best
5. **Keep or revert** — if improved, keep; otherwise revert to previous state
6. **Repeat** — loop continuously (~12 experiments/hour in [[autoresearch]])

## Key design principles

- **Single metric**: one number to optimize, enabling unambiguous keep/revert decisions
- **Fixed budget**: every run uses the same time/compute, making results directly comparable across parameter changes
- **Single modification scope**: the agent edits one file/config, keeping changes reviewable and revertable
- **Self-contained**: no external dependencies or complex orchestration

## Applications

### LLM training (original context)

[[autoresearch]] applies this loop to GPT training: agent modifies `train.py` (architecture, hyperparameters, optimizer), trains for 5 minutes, evaluates val_bpb, keeps or reverts.

### Protein binder design (proposed)

The same pattern maps to [[rfdiffusion3]] DNA binder optimization. See [[autoresearch-for-binder-design]] for the full mapping:

| LLM training | Binder design |
|---|---|
| Modify `train.py` | Modify RFD3 config (contig, length, ori_token, H-bond constraints) |
| 5-min training run | RFD3 generation + RF3 scoring |
| val_bpb metric | ipTM score (protein-DNA complex confidence) |
| Keep/revert | Keep parameter set if best ipTM improves |

## See also

- [[autoresearch]] — the original framework by Karpathy
- [[autoresearch-for-binder-design]] — applying the pattern to RFD3
