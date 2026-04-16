---
type: source-summary
title: "Autoresearch (Karpathy)"
created: 2026-04-16
updated: 2026-04-16
sources: []
tags: [tool, ai-agent, methodology, open-source]
aliases: []
source_file: "../raw/articles/autoresearch-karpathy.md"
source_kind: url
source_date: 2026-03-01
see_also: "../raw/articles/autoresearch-program-md.md"
---

# Autoresearch (Karpathy)

GitHub repository by Andrej Karpathy introducing autonomous AI agent-driven machine learning experimentation.

## Source

- **URL**: https://github.com/karpathy/autoresearch
- **Author**: Andrej Karpathy
- **Date**: March 2026
- **License**: MIT

## Summary

Autoresearch implements an [[autonomous-experiment-loop]]: an AI agent modifies a training script, runs a 5-minute experiment, evaluates the result (val_bpb), and keeps improvements or reverts failures. Running overnight on a single GPU produces ~100 autonomous experiments.

## Key contributions

1. **Concrete implementation** of agent-driven research — not theoretical, but a working system that produces real LLM training improvements overnight.
2. **program.md pattern** — human writes high-level research objectives in markdown; agent interprets and executes. The human programs the research direction, not the code.
3. **Fixed-budget comparability** — 5-minute wall-clock budget makes every experiment directly comparable regardless of what the agent changed.
4. **Single-file scope** — agent only touches `train.py`, keeping changes reviewable and revertable. Minimal blast radius.

## Design pattern (generalizable)

The core loop is domain-agnostic:

1. Agent reads objectives from instruction file
2. Agent modifies configuration/code
3. System runs experiment with fixed budget
4. System evaluates single metric
5. Keep if improved, revert if not
6. Repeat

This pattern applies beyond LLM training to any domain with: a parameterized experiment, a computable metric, and a fixed compute budget per trial.

## Key reference file

The `program.md` file (saved to `raw/articles/autoresearch-program-md.md`) is the core instruction template. Key patterns to port to binder design:

- "LOOP FOREVER" — autonomous agent runs indefinitely until interrupted
- "NEVER STOP" — do not ask for human confirmation between experiments
- Keep/revert on single metric — unambiguous decision criterion
- Log everything to TSV — full experiment audit trail
- Git branch per run — isolate experiment history
- Fixed time budget — makes all experiments comparable

## Wiki pages generated

- [[autoresearch]], [[autonomous-experiment-loop]], [[autoresearch-for-binder-design]]
