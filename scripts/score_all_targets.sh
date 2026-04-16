#!/bin/bash
# Score all DNA targets from the binder CSV using RF3
# Usage: bash scripts/score_all_targets.sh

CSV="raw/data/RFD3 binders for Genome Editing Assay -BakerLab.csv"
OUTDIR="analysis_output/scores"
mkdir -p "$OUTDIR"

declare -A TARGETS
TARGETS[PNRP1]="TGAGGAGAGGAG"
TARGETS[CAG]="CAGCAGCAGCAG"
TARGETS[HSTELO]="AGGGTTAGGGTT"
TARGETS[OCT4pt1]="GGTGAAATGA"
TARGETS[OCT4pt2]="GGGCTTGCGA"
TARGETS[NFKB]="GGGGATTCCCCC"
TARGETS[HD]="GCTTAATTAGCG"
TARGETS[TATA]="CGTATAAACG"
TARGETS[Dux4grna2]="CAGGCCGCAGG"

for NAME in "${!TARGETS[@]}"; do
    SEQ="${TARGETS[$NAME]}"
    echo "=== Scoring $NAME ($SEQ) ==="
    uv run python scripts/score_complexes.py \
        --binder-csv "$CSV" \
        --dna-sequence "$SEQ" \
        --target-filter "$SEQ" \
        --output "$OUTDIR/${NAME}_scores.tsv" \
        --rf3-output-dir "/tmp/rf3_${NAME}"
    echo ""
done

echo "All scores written to $OUTDIR/"
