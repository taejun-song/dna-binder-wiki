# autoresearch

**Source**: https://github.com/karpathy/autoresearch
**Author**: Andrej Karpathy
**Date**: March 2026

The idea: give an AI agent a small but real LLM training setup and let it experiment autonomously overnight. It modifies the code, trains for 5 minutes, checks if the result improved, keeps or discards, and repeats. You wake up in the morning to a log of experiments and (hopefully) a better model.

## How it works

The repo is deliberately kept small and only really has three files that matter:

- **`prepare.py`** — fixed constants, one-time data prep (downloads training data, trains a BPE tokenizer), and runtime utilities (dataloader, evaluation). Not modified.
- **`train.py`** — the single file the agent edits. Contains the full GPT model, optimizer (Muon + AdamW), and training loop. Everything is fair game: architecture, hyperparameters, optimizer, batch size, etc. This file is edited and iterated on by the agent.
- **`program.md`** — baseline instructions for one agent. Point your agent here and let it go. This file is edited and iterated on by the human.

By design, training runs for a **fixed 5-minute time budget** (wall clock, excluding startup/compilation), regardless of the details of your compute. The metric is **val_bpb** (validation bits per byte) — lower is better, and vocab-size-independent so architectural changes are fairly compared.

## Design choices

- **Single file to modify.** The agent only touches `train.py`. This keeps the scope manageable and diffs reviewable.
- **Fixed time budget.** Training always runs for exactly 5 minutes, regardless of your specific platform. This means you can expect approx 12 experiments/hour and approx 100 experiments while you sleep. Two upsides: (1) makes experiments directly comparable regardless of what the agent changes (model size, batch size, architecture, etc), (2) autoresearch will find the most optimal model for your platform in that time budget.
- **Self-contained.** No external dependencies beyond PyTorch and a few small packages. No distributed training, no complex configs. One GPU, one file, one metric.

## Core loop

1. Agent reads `program.md` for objectives
2. Agent modifies `train.py`
3. Training runs for exactly 5 minutes
4. Evaluate val_bpb (lower is better)
5. Keep if improved, revert if not
6. Repeat (~12 experiments/hour, ~100 overnight)
