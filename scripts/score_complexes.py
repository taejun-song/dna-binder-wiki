#!/usr/bin/env python3
"""Score protein-DNA complexes using RoseTTAFold3 for pTM and ipTM.

Requires: rc-foundry[all] installed, model checkpoints downloaded.
Run on GPU server.

Usage:
    # Score all binders in a directory against their DNA target
    python scripts/score_complexes.py \
        --binder-dir analysis_output/generated/PNRP1 \
        --dna-sequence TGAGGAGAGGAG \
        --output analysis_output/scores/PNRP1_scores.tsv
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def make_rf3_input(protein_seq: str, dna_seq: str, name: str) -> dict:
    return {
        "name": name,
        "components": [
            {"seq": protein_seq, "chain_id": "A"},
            {"seq": dna_seq, "chain_id": "B"},
        ],
    }


def extract_sequence_from_pdb(pdb_path: str) -> str:
    aa_map = {
        "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
        "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
        "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
        "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
    }
    residues = {}
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                chain = line[21]
                resnum = int(line[22:26].strip())
                resname = line[17:20].strip()
                if chain not in ("B", "C"):  # skip DNA chains
                    residues[(chain, resnum)] = aa_map.get(resname, "X")
    return "".join(v for _, v in sorted(residues.items()))


def parse_rf3_confidences(summary_path: str) -> dict:
    with open(summary_path) as f:
        data = json.load(f)
    return {
        "ptm": data.get("ptm", 0.0),
        "iptm": data.get("iptm", 0.0),
        "ranking_score": data.get("ranking_score", 0.0),
    }


def main():
    parser = argparse.ArgumentParser(description="Score protein-DNA complexes with RF3")
    parser.add_argument("--binder-csv", help="CSV with binder sequences (amino acid sequence column)")
    parser.add_argument("--binder-dir", help="Directory of binder PDB files")
    parser.add_argument("--dna-sequence", required=True, help="Target DNA sequence")
    parser.add_argument("--target-filter", help="Only include rows where on_target_seq matches this value")
    parser.add_argument("--output", required=True, help="Output TSV path")
    parser.add_argument("--rf3-output-dir", default="/tmp/rf3_scoring", help="RF3 working directory")
    args = parser.parse_args()

    rf3_dir = Path(args.rf3_output_dir)
    rf3_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = []
    if args.binder_csv:
        import pandas as pd
        df = pd.read_csv(args.binder_csv)
        if args.target_filter and "on_target_seq" in df.columns:
            df = df[df["on_target_seq"] == args.target_filter]
            print(f"Filtered to {len(df)} rows matching target {args.target_filter}", file=sys.stderr)
        for _, row in df.iterrows():
            candidates.append({
                "name": row.get("shorthand_name", row.get("design_name", f"design_{_}")),
                "sequence": row["amino acid sequence"],
            })
    elif args.binder_dir:
        for pdb in sorted(Path(args.binder_dir).glob("*.pdb")):
            seq = extract_sequence_from_pdb(str(pdb))
            if seq:
                candidates.append({"name": pdb.stem, "sequence": seq})

    if not candidates:
        print("No candidates found", file=sys.stderr)
        sys.exit(1)

    print(f"Scoring {len(candidates)} candidates with RF3...", file=sys.stderr)

    rf3_inputs = [
        make_rf3_input(c["sequence"], args.dna_sequence, c["name"])
        for c in candidates
    ]
    input_path = rf3_dir / "rf3_inputs.json"
    with open(input_path, "w") as f:
        json.dump(rf3_inputs, f, indent=2)

    cmd = ["rf3", "fold", f"inputs={input_path}", f"out_dir={rf3_dir}/results"]
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"RF3 failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(1)

    results_dir = rf3_dir / "results"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["name", "sequence_length", "ptm", "iptm", "ranking_score"])
        for c in candidates:
            summary = list(results_dir.glob(f"**/{c['name']}*summary_confidences.json"))
            if summary:
                scores = parse_rf3_confidences(str(summary[0]))
                writer.writerow([
                    c["name"],
                    len(c["sequence"]),
                    f"{scores['ptm']:.4f}",
                    f"{scores['iptm']:.4f}",
                    f"{scores['ranking_score']:.4f}",
                ])
                print(f"  {c['name']}: pTM={scores['ptm']:.3f}, ipTM={scores['iptm']:.3f}", file=sys.stderr)
            else:
                writer.writerow([c["name"], len(c["sequence"]), "NA", "NA", "NA"])
                print(f"  {c['name']}: no RF3 output found", file=sys.stderr)

    print(f"Scores written to {output_path}")


if __name__ == "__main__":
    main()
