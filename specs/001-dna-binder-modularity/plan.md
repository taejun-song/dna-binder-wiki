# Implementation Plan: Modular DNA-Binding Protein Discovery

**Branch**: `001-dna-binder-modularity` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-dna-binder-modularity/spec.md`

## Summary

Build a Python analysis pipeline that takes RFD3-generated DNA-binding protein candidates, deduplicates them, predicts structures via ESMFold, clusters by redundancy, identifies conserved DNA-recognition modules, and outputs findings as wiki pages following CLAUDE.md conventions.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ESMFold (via HuggingFace `esm` or ESM API), BioPython, NumPy, pandas
**Storage**: Files (CSV input, PDB output from ESMFold, markdown wiki pages)
**Testing**: pytest
**Target Platform**: macOS / Linux (local execution)
**Project Type**: Analysis pipeline (CLI scripts)
**Performance Goals**: Process ~100 candidates per target within reasonable time; ESMFold inference is the bottleneck (~10-30s per sequence on GPU, minutes on CPU)
**Constraints**: ESMFold requires GPU for practical speed on 100+ sequences; CPU fallback is viable for small batches (<20)
**Scale/Scope**: 92 candidates across 9 targets in current dataset; largest target (PNRP1) has 38 candidates

## Constitution Check

*GATE: Constitution is an unfilled template — no project-specific gates defined. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/001-dna-binder-modularity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
analysis/
├── __init__.py
├── normalize.py         # Step 1: dedup, name standardization
├── predict.py           # Step 2: ESMFold structure prediction
├── quality.py           # Step 3: pLDDT filtering, plausibility checks
├── similarity.py        # Step 4: pairwise sequence + structural comparison
├── redundancy.py        # Step 5: clustering, origin classification
├── interface.py         # Step 6: DNA-contact residue prediction
├── modules.py           # Step 7: module identification, conservation analysis
├── modularity.py        # Step 8: transferability assessment
├── wiki_output.py       # Step 9: generate wiki pages per CLAUDE.md
├── pipeline.py          # Orchestrator: run full pipeline per target
└── utils.py             # Shared helpers (sequence I/O, alignment)

tests/
├── test_normalize.py
├── test_similarity.py
├── test_redundancy.py
├── test_modules.py
└── fixtures/
    └── sample_candidates.csv

scripts/
└── run_analysis.py      # CLI entry point
```

**Structure Decision**: Single-project Python package. No web frontend or API — this is a batch analysis pipeline invoked from the command line, producing wiki markdown files as output.
