# Quickstart: Modular DNA-Binding Protein Discovery

**Date**: 2026-04-16 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Python 3.11+
- GPU recommended for ESMFold (CPU works for small batches)
- ~8GB disk space for ESMFold model weights (downloaded on first run)

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install torch esm biopython numpy pandas tmtools freesasa

# Verify ESMFold availability
python -c "import esm; print('ESMFold available')"
```

## Run Analysis

```bash
# Analyze a single DNA target (e.g., PNRP1 with 38 candidates)
python scripts/run_analysis.py \
  --input raw/data/RFD3\ binders\ for\ Genome\ Editing\ Assay\ -BakerLab.csv \
  --target TGAGGAGAGGAG \
  --output-dir analysis_output/

# Analyze all targets in the dataset
python scripts/run_analysis.py \
  --input raw/data/RFD3\ binders\ for\ Genome\ Editing\ Assay\ -BakerLab.csv \
  --all-targets \
  --output-dir analysis_output/
```

## Output

The pipeline produces:
1. **ESMFold predictions**: PDB files in `analysis_output/structures/`
2. **Intermediate data**: CSV files with annotations in `analysis_output/data/`
3. **Wiki pages**: Markdown files ready for placement into wiki directories

Wiki pages are generated but not automatically placed — the wiki maintainer workflow (CLAUDE.md §6.1) handles final placement, index regeneration, and log updates.

## Run Tests

```bash
pytest tests/ -v
```

## Pipeline Stages (Quick Reference)

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| 1. Normalize | normalize.py | CSV | deduplicated candidates |
| 2. Predict | predict.py | sequences | PDB files + pLDDT scores |
| 3. Filter | quality.py | pLDDT scores | filtered candidate set |
| 4. Similarity | similarity.py | sequences + PDBs | pairwise similarity matrix |
| 5. Cluster | redundancy.py | similarity matrix | redundancy clusters |
| 6. Interface | interface.py | PDBs + clusters | contact residue annotations |
| 7. Modules | modules.py | annotations + alignment | module definitions |
| 8. Assess | modularity.py | modules | transferability report |
| 9. Output | wiki_output.py | all above | wiki markdown pages |
