---
type: concept
title: "Classifier-Free Guidance"
created: 2026-04-16
updated: 2026-04-16
sources:
  - "[[rfdiffusion3-paper]]"
tags: [diffusion, conditioning, generative-model]
aliases: [CFG]
---

# Classifier-Free Guidance

A technique where each denoising step performs two forward passes — one conditioned and one unconditional — and the final update is a weighted combination that amplifies adherence to the conditioning signal.

## Origin

Classifier-free guidance was introduced by Ho & Salimans (2022) in the context of image diffusion. It eliminates the need for a separately trained classifier to steer generation, instead training a single model that can operate with or without conditioning by randomly dropping the conditioning input during training.

## Application in protein design

[[rfdiffusion3]] applies classifier-free guidance to improve satisfaction of atom-level constraints such as hydrogen-bond donor/acceptor labels, solvent-accessible surface area specifications, and functional motif coordinates. At each denoising step the network runs twice: once with the full conditioning and once without. The weighted average steers the generated structure toward designs that better respect the input constraints.

## Impact on RFD3 benchmarks

- Small-molecule binder design: hydrogen-bonding interaction rate increased from 32.67% (conditioned, no CFG) to 36.67% (with CFG).
- DNA hydrogen bonds to bases: 11.3% baseline vs 12.5% with CFG.
- Consistent improvements across all conditioning modalities tested.

## See also

- [[all-atom-diffusion]] — the diffusion framework where CFG is applied
- [[rfdiffusion3]] — the model that uses CFG for protein design
