#!/usr/bin/env python3
"""Generate target-specific DNA PDB files by stripping 1BNA to backbone-only.

RFD3 reads the full atomic structure from the input PDB. Since we can't easily
swap purine/pyrimidine bases without breaking atom counts, we instead:
1. Keep only backbone atoms (P, OP1, OP2, O5', C5', C4', O4', C3', O3', C2', C1')
   which are identical across all nucleotides
2. Rename residues to match the target sequence
3. RFD3 uses the backbone geometry to condition protein generation;
   the base identity comes from the contig specification

For targets with <12bp, we trim residues from the ends.

Output: data/dna_templates/{TARGET}.pdb
"""
import sys
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}
COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}
BASE_TO_RES = {"A": " DA", "T": " DT", "G": " DG", "C": " DC"}
DNA_RESNAMES = {" DA", " DT", " DG", " DC"}
BACKBONE_ATOMS = {
    "P", "OP1", "OP2", "O5'", "C5'", "C4'", "O4'", "C3'", "O3'", "C2'", "C1'",
}


def make_target_pdb(template_path, target_name, seq, out_path):
    comp_seq = "".join(COMPLEMENT[b] for b in reversed(seq))
    n = len(seq)
    with open(template_path) as f:
        lines = f.readlines()

    chain_a_resnums = sorted({
        int(line[22:26].strip())
        for line in lines
        if line.startswith("ATOM") and len(line) >= 26 and line[21] == "A" and line[17:20] in DNA_RESNAMES
    })
    chain_b_resnums = sorted({
        int(line[22:26].strip())
        for line in lines
        if line.startswith("ATOM") and len(line) >= 26 and line[21] == "B" and line[17:20] in DNA_RESNAMES
    })

    a_keep = set(chain_a_resnums[:n])
    b_keep = set(chain_b_resnums[:n])
    a_map = {chain_a_resnums[i]: seq[i] for i in range(min(n, len(chain_a_resnums)))}
    b_map = {chain_b_resnums[i]: comp_seq[i] for i in range(min(n, len(chain_b_resnums)))}

    out_lines = []
    out_lines.append(f"REMARK   Target: {target_name}  Sequence: {seq}\n")
    out_lines.append(f"REMARK   Backbone from 1BNA, residues renamed for target\n")
    for line in lines:
        if not line.startswith("ATOM") or len(line) < 26:
            if line.startswith(("TER", "END")):
                out_lines.append(line)
            continue
        chain = line[21]
        resname = line[17:20]
        if resname not in DNA_RESNAMES:
            continue
        resnum = int(line[22:26].strip())
        atom_name = line[12:16].strip()
        if atom_name not in BACKBONE_ATOMS:
            continue
        if chain == "A" and resnum in a_keep and resnum in a_map:
            new_res = BASE_TO_RES[a_map[resnum]]
            line = line[:17] + new_res + line[20:]
            out_lines.append(line)
        elif chain == "B" and resnum in b_keep and resnum in b_map:
            new_res = BASE_TO_RES[b_map[resnum]]
            line = line[:17] + new_res + line[20:]
            out_lines.append(line)

    if not out_lines[-1].startswith("END"):
        out_lines.append("END\n")
    Path(out_path).write_text("".join(out_lines))
    return n


def main():
    template = Path("data/dna_templates/1BNA.pdb")
    if not template.exists():
        print(f"ERROR: {template} not found", file=sys.stderr)
        sys.exit(1)
    out_dir = Path("data/dna_templates")
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(TARGETS.keys())
    for name in targets:
        seq = TARGETS[name]
        out_path = out_dir / f"{name}.pdb"
        n = make_target_pdb(template, name, seq, out_path)
        print(f"{name}: {seq} ({n}bp) -> {out_path}")


if __name__ == "__main__":
    main()
