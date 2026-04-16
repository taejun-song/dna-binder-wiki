#!/usr/bin/env python3
"""Generate DNA binders for all targets in parallel using RFD3 + score with RF3.

Creates ideal B-DNA PDB structures, runs RFD3 to generate binders,
assigns sequences with LigandMPNN, and scores with RF3 for pTM/ipTM.

Usage:
    python scripts/generate_all_targets.py \
        --num-designs 50 \
        --output-dir analysis_output/gen2 \
        --parallel 4
"""
import argparse
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG",
    "CAG": "CAGCAGCAGCAG",
    "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA",
    "OCT4pt2": "GGGCTTGCGA",
    "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG",
    "TATA": "CGTATAAACG",
    "Dux4grna2": "CAGGCCGCAGG",
}

COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}
BASE_TO_RES = {"A": "DA", "T": "DT", "G": "DG", "C": "DC"}


def generate_ideal_bdna_pdb(sequence: str, output_path: Path) -> Path:
    """Generate ideal B-DNA double-stranded PDB from sequence."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comp_seq = "".join(COMPLEMENT[b] for b in reversed(sequence))
    rise = 3.38
    twist = math.radians(36.0)
    radius = 10.0
    lines = []
    atom_idx = 1
    for i, base in enumerate(sequence):
        z = i * rise
        angle = i * twist
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        resname = BASE_TO_RES[base]
        resnum = i + 1
        lines.append(
            f"ATOM  {atom_idx:5d}  C1' {resname} A{resnum:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"
        )
        atom_idx += 1
    for i, base in enumerate(comp_seq):
        z = (len(sequence) - 1 - i) * rise
        angle = (len(sequence) - 1 - i) * twist + math.radians(180.0)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        resname = BASE_TO_RES[base]
        resnum = i + 1
        lines.append(
            f"ATOM  {atom_idx:5d}  C1' {resname} B{resnum:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"
        )
        atom_idx += 1
    lines.append("END")
    output_path.write_text("\n".join(lines))
    return output_path


def create_rfd3_config(
    name: str,
    dna_pdb: str,
    dna_len: int,
    num_designs: int,
    protein_length: str = "120-140",
    output_dir: Path = Path("."),
) -> Path:
    """Create RFD3 JSON input config for DNA binder design."""
    contig = f"A1-{dna_len},/0,B1-{dna_len},/0,{protein_length}"
    config = {
        name: {
            "input": str(Path(dna_pdb).resolve()),
            "contig": contig,
            "length": protein_length,
            "is_non_loopy": True,
        }
    }
    config_path = output_dir / f"{name}_rfd3_config.json"
    config_path.write_text(json.dumps(config, indent=2))
    return config_path


def run_rfd3_for_target(
    name: str,
    sequence: str,
    num_designs: int,
    output_dir: Path,
    checkpoint: str,
    protein_length: str = "120-140",
) -> dict:
    """Run RFD3 generation for a single target."""
    target_dir = output_dir / name
    target_dir.mkdir(parents=True, exist_ok=True)

    dna_pdb = target_dir / f"{name}_dna.pdb"
    generate_ideal_bdna_pdb(sequence, dna_pdb)

    config_path = create_rfd3_config(
        name=name,
        dna_pdb=str(dna_pdb),
        dna_len=len(sequence),
        num_designs=num_designs,
        protein_length=protein_length,
        output_dir=target_dir,
    )

    rfd3_bin = str(Path(sys.executable).parent / "rfd3")
    rfd3_out = target_dir / "rfd3_output"
    cmd = [
        rfd3_bin,
        f"out_dir={rfd3_out}",
        f"inputs={config_path}",
        f"n_batches={num_designs}",
        f"ckpt_path={checkpoint}",
    ]

    log_path = target_dir / "rfd3.log"
    print(f"[{name}] Launching RFD3: {num_designs} designs, length={protein_length}", file=sys.stderr)
    with open(log_path, "w") as logf:
        result = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)

    pdbs = list(rfd3_out.rglob("*.pdb")) if rfd3_out.exists() else []
    print(f"[{name}] RFD3 done: {len(pdbs)} PDBs generated (exit={result.returncode})", file=sys.stderr)

    return {
        "name": name,
        "sequence": sequence,
        "num_pdbs": len(pdbs),
        "output_dir": str(target_dir),
        "exit_code": result.returncode,
    }


def score_with_rf3(name: str, target_dir: Path, dna_sequence: str) -> dict:
    """Score generated binders with RF3 for pTM/ipTM."""
    rf3_bin = str(Path(sys.executable).parent / "rf3")
    rfd3_out = target_dir / "rfd3_output"
    pdbs = sorted(rfd3_out.rglob("*.pdb")) if rfd3_out.exists() else []

    if not pdbs:
        return {"name": name, "scores": []}

    from scripts.score_complexes import extract_sequence_from_pdb, make_rf3_input

    rf3_inputs = []
    for pdb in pdbs:
        seq = extract_sequence_from_pdb(str(pdb))
        if seq:
            rf3_inputs.append(make_rf3_input(seq, dna_sequence, pdb.stem))

    if not rf3_inputs:
        return {"name": name, "scores": []}

    rf3_dir = target_dir / "rf3_scoring"
    rf3_dir.mkdir(exist_ok=True)
    input_path = rf3_dir / "rf3_inputs.json"
    input_path.write_text(json.dumps(rf3_inputs, indent=2))

    cmd = [rf3_bin, "fold", f"inputs={input_path}", f"out_dir={rf3_dir}/results"]
    log_path = target_dir / "rf3.log"
    print(f"[{name}] Launching RF3 scoring for {len(rf3_inputs)} designs...", file=sys.stderr)
    with open(log_path, "w") as logf:
        subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)

    return {"name": name, "num_scored": len(rf3_inputs)}


def main():
    parser = argparse.ArgumentParser(description="Generate DNA binders for all targets")
    parser.add_argument("--num-designs", type=int, default=50, help="Designs per target")
    parser.add_argument("--output-dir", default="analysis_output/gen2", help="Output directory")
    parser.add_argument("--parallel", type=int, default=3, help="Parallel RFD3 processes")
    parser.add_argument("--protein-length", default="120-140", help="Protein length range")
    parser.add_argument("--checkpoint", default=os.path.expanduser("~/.foundry/checkpoints/rfd3_latest.ckpt"))
    parser.add_argument("--targets", nargs="*", default=None, help="Specific targets (default: all)")
    parser.add_argument("--skip-scoring", action="store_true", help="Skip RF3 scoring")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = {k: v for k, v in TARGETS.items() if args.targets is None or k in args.targets}
    print(f"Generating {args.num_designs} designs for {len(targets)} targets with {args.parallel} parallel processes", file=sys.stderr)

    # Phase 1: Generate with RFD3 in parallel
    results = []
    with ProcessPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(
                run_rfd3_for_target,
                name, seq, args.num_designs, output_dir,
                args.checkpoint, args.protein_length,
            ): name
            for name, seq in targets.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[{name}] FAILED: {e}", file=sys.stderr)

    # Phase 2: Score with RF3 (sequential — shares GPU)
    if not args.skip_scoring:
        for r in results:
            if r["num_pdbs"] > 0:
                score_with_rf3(r["name"], Path(r["output_dir"]), r["sequence"])

    # Summary
    print("\n" + "=" * 60)
    for r in sorted(results, key=lambda x: x["name"]):
        print(f"{r['name']}: {r['num_pdbs']} PDBs generated (exit={r['exit_code']})")


if __name__ == "__main__":
    main()
