#!/usr/bin/env python3
"""Generate target-specific DNA PDB files by mutating 1BNA.

Takes the real 1BNA.pdb crystal structure and replaces the DNA sequence
while keeping all backbone atoms and geometry intact. This preserves
perfect PDB formatting that RFD3 can parse.

For sequences shorter than 12bp, we trim residues from the ends.
For sequences exactly 12bp, we do a direct substitution.

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


def mutate_1bna(template_path, target_name, seq, out_path):
    """Mutate 1BNA residue names to match target sequence."""
    comp_seq = "".join(COMPLEMENT[b] for b in reversed(seq))
    n = len(seq)
    with open(template_path) as f:
        lines = f.readlines()
    dna_resnames = {" DA", " DT", " DG", " DC"}
    chain_a_residues = set()
    chain_b_residues = set()
    for line in lines:
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 26:
            chain = line[21]
            resnum = int(line[22:26].strip())
            resname = line[17:20]
            if resname not in dna_resnames:
                continue
            if chain == "A":
                chain_a_residues.add(resnum)
            elif chain == "B":
                chain_b_residues.add(resnum)
    a_resnums = sorted(chain_a_residues)
    b_resnums = sorted(chain_b_residues)
    a_keep = set(a_resnums[:n])
    b_keep = set(b_resnums[:n])
    a_map = {a_resnums[i]: seq[i] for i in range(min(n, len(a_resnums)))}
    b_map = {b_resnums[i]: comp_seq[i] for i in range(min(n, len(b_resnums)))}

    out_lines = []
    out_lines.append(f"REMARK   Target: {target_name}  Sequence: {seq}\n")
    out_lines.append(f"REMARK   Mutated from 1BNA template\n")
    for line in lines:
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 26:
            chain = line[21]
            resnum = int(line[22:26].strip())
            resname = line[17:20]
            if resname not in dna_resnames:
                continue
            if chain == "A" and resnum in a_keep and resnum in a_map:
                new_res = BASE_TO_RES[a_map[resnum]]
                line = line[:17] + new_res + line[20:]
                out_lines.append(line)
            elif chain == "B" and resnum in b_keep and resnum in b_map:
                new_res = BASE_TO_RES[b_map[resnum]]
                line = line[:17] + new_res + line[20:]
                out_lines.append(line)
        elif line.startswith("TER"):
            out_lines.append(line)
        elif line.startswith("END"):
            out_lines.append(line)

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
        n = mutate_1bna(template, name, seq, out_path)
        print(f"{name}: {seq} ({n}bp) -> {out_path}")


if __name__ == "__main__":
    main()
