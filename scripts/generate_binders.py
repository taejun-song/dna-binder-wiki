#!/usr/bin/env python3
"""Generate DNA-binding protein binders using RFdiffusion3 via rc-foundry.

Requires: rc-foundry[all] installed, model checkpoints downloaded.
Run on GPU server.

Usage:
    # Generate binders for PNRP1 target (needs DNA structure PDB)
    python scripts/generate_binders.py \
        --dna-pdb data/dna_targets/PNRP1.pdb \
        --dna-chains A,B \
        --dna-residues A1-6,B1-6 \
        --num-designs 50 \
        --protein-length 120-140 \
        --output-dir analysis_output/generated/PNRP1 \
        --checkpoint ~/.foundry/checkpoints/rfd3_latest.ckpt
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def make_rfd3_config(
    dna_pdb: str,
    dna_residues: str,
    protein_length: str,
    ori_token: list[int] | None = None,
) -> dict:
    config = {
        "dna_binder": {
            "input": dna_pdb,
            "contig": f"{dna_residues},/0,{protein_length}",
            "is_non_loopy": True,
        }
    }
    if ori_token:
        config["dna_binder"]["ori_token"] = ori_token
    return config


def main():
    parser = argparse.ArgumentParser(description="Generate DNA binders with RFdiffusion3")
    parser.add_argument("--dna-pdb", required=True, help="Path to target DNA structure PDB")
    parser.add_argument("--dna-chains", default="A,B", help="DNA chain IDs (comma-separated)")
    parser.add_argument("--dna-residues", required=True, help="DNA residue contig (e.g., A1-6,/0,B1-6)")
    parser.add_argument("--num-designs", type=int, default=50, help="Number of designs to generate")
    parser.add_argument("--protein-length", default="120-140", help="Protein length range")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--checkpoint", default=None, help="Path to RFD3 checkpoint")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = make_rfd3_config(
        dna_pdb=args.dna_pdb,
        dna_residues=args.dna_residues,
        protein_length=args.protein_length,
    )

    config_path = output_dir / "rfd3_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    rfd3_bin = str(Path(sys.executable).parent / "rfd3")
    cmd = [
        rfd3_bin,
        f"out_dir={output_dir}",
        f"inputs={config_path}",
        f"inference.num_designs={args.num_designs}",
    ]
    if args.checkpoint:
        cmd.append(f"ckpt_path={args.checkpoint}")

    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"RFD3 failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(1)

    pdbs = list(output_dir.glob("**/*.pdb"))
    print(f"Generated {len(pdbs)} PDB files in {output_dir}")


if __name__ == "__main__":
    main()
