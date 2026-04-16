---
type: entity
title: "Autoresearch"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[autoresearch-karpathy]]"
tags: [tool, ai-agent, methodology, karpathy]
aliases: []
---

# Autoresearch

An open-source framework by Andrej Karpathy that delegates machine learning research to autonomous AI agents, implementing the [[autonomous-experiment-loop]] pattern.

## Overview

Released in March 2026, autoresearch gives an AI agent a small LLM training setup and lets it experiment overnight. The agent modifies code, trains for 5 minutes, checks if the result improved, keeps or discards, and repeats. ~12 experiments/hour, ~100 overnight on a single GPU.

## Architecture

Three files:

- `prepare.py` — data prep and evaluation utilities (not modified by agent)
- `train.py` — full GPT model, optimizer, training loop (agent modifies this)
- `program.md` — human-written instructions that guide agent behavior

## Design choices

- **Single file to modify**: keeps scope manageable and diffs reviewable
- **Fixed 5-minute time budget**: makes experiments directly comparable regardless of parameter changes
- **val_bpb metric**: bits-per-byte is vocabulary-size-independent, enabling fair comparison across architectural changes
- **Self-contained**: single GPU, no distributed training, no complex configs

## Relevance to this wiki

The autoresearch pattern can be adapted to protein design parameter optimization. See [[autoresearch-for-binder-design]] for applying this to [[rfdiffusion3]] DNA binder design with ipTM as the optimization metric.

## See also

- [[autonomous-experiment-loop]] — the general methodology pattern
