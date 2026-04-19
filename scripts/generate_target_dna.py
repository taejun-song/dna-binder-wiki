#!/usr/bin/env python3
"""Generate ideal B-DNA PDB files for each target sequence.

Uses standard B-DNA parameters (rise=3.38A, twist=36deg) to build
double-stranded DNA from the target sequence. Each nucleotide is represented
with backbone atoms (P, O5', C5', C4', C3', O3') and base atoms positioned
using standard B-DNA geometry derived from the 1BNA crystal structure.

Output: data/dna_templates/{TARGET}.pdb for each target.
"""
import math
import sys
from pathlib import Path

import numpy as np

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}

COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}
RES_NAME = {"A": "DA", "T": "DT", "G": "DG", "C": "DC"}

RISE = 3.38
TWIST_DEG = 36.0
TWIST_RAD = math.radians(TWIST_DEG)
RADIUS = 10.0
INCLINATION = math.radians(0.0)


def build_base_atoms(base):
    """Return relative atom positions for a nucleotide (backbone + base stub)."""
    atoms = []
    atoms.append(("P", np.array([0.0, 8.9, 0.0])))
    atoms.append(("OP1", np.array([0.7, 10.2, 0.0])))
    atoms.append(("OP2", np.array([-0.7, 10.2, 0.0])))
    atoms.append(("O5'", np.array([0.0, 7.6, 1.2])))
    atoms.append(("C5'", np.array([0.0, 6.2, 1.2])))
    atoms.append(("C4'", np.array([0.0, 5.5, 0.0])))
    atoms.append(("O4'", np.array([1.2, 5.0, 0.0])))
    atoms.append(("C3'", np.array([-1.0, 4.3, 0.0])))
    atoms.append(("O3'", np.array([-1.0, 3.0, 0.0])))
    atoms.append(("C2'", np.array([0.0, 3.8, 0.9])))
    atoms.append(("C1'", np.array([1.2, 4.0, 0.0])))
    if base in ("A", "G"):
        atoms.append(("N9", np.array([2.4, 3.5, 0.0])))
        atoms.append(("C8", np.array([3.5, 4.2, 0.0])))
        atoms.append(("N7", np.array([4.6, 3.5, 0.0])))
        atoms.append(("C5", np.array([4.3, 2.1, 0.0])))
        atoms.append(("C6", np.array([5.2, 1.0, 0.0])))
        atoms.append(("N1", np.array([4.7, -0.2, 0.0])))
        atoms.append(("C2", np.array([3.4, -0.3, 0.0])))
        atoms.append(("N3", np.array([2.5, 0.6, 0.0])))
        atoms.append(("C4", np.array([3.0, 1.8, 0.0])))
        if base == "A":
            atoms.append(("N6", np.array([6.5, 1.1, 0.0])))
        else:
            atoms.append(("O6", np.array([6.4, 1.1, 0.0])))
            atoms.append(("N2", np.array([3.0, -1.5, 0.0])))
    else:
        atoms.append(("N1", np.array([2.4, 3.5, 0.0])))
        atoms.append(("C2", np.array([3.5, 4.2, 0.0])))
        atoms.append(("O2", np.array([3.5, 5.4, 0.0])))
        atoms.append(("N3", np.array([4.6, 3.5, 0.0])))
        atoms.append(("C4", np.array([4.6, 2.1, 0.0])))
        atoms.append(("C5", np.array([3.4, 1.4, 0.0])))
        atoms.append(("C6", np.array([2.4, 2.1, 0.0])))
        if base == "C":
            atoms.append(("N4", np.array([5.7, 1.5, 0.0])))
        else:
            atoms.append(("O4", np.array([5.7, 1.5, 0.0])))
            atoms.append(("C7", np.array([3.3, 0.0, 0.0])))
    return atoms


def rotation_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def build_strand(seq, chain_id, start_resnum, is_complementary=False):
    """Build one strand of B-DNA."""
    lines = []
    atom_num = 1
    n = len(seq)
    for i, base in enumerate(seq):
        resname = RES_NAME[base]
        resnum = start_resnum + i
        angle = i * TWIST_RAD
        if is_complementary:
            angle += math.pi
        z_offset = i * RISE
        if is_complementary:
            z_offset = (n - 1 - i) * RISE
        rot = rotation_z(angle)
        base_atoms = build_base_atoms(base)
        for atom_name, rel_pos in base_atoms:
            pos = rot @ rel_pos
            pos[2] += z_offset
            lines.append(
                f"ATOM  {atom_num:5d}  {atom_name:<4s}{resname:>3s} {chain_id}{resnum:4d}    "
                f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}  1.00  0.00           "
                f"{atom_name[0]:>2s}"
            )
            atom_num += 1
    return lines, atom_num


def generate_dna_pdb(target_name, seq, out_path):
    comp_seq = "".join(COMPLEMENT[b] for b in reversed(seq))
    lines = []
    lines.append(f"REMARK   Target: {target_name}  Sequence: {seq}")
    lines.append(f"REMARK   Ideal B-DNA generated for RFD3 input")
    strand1_lines, _ = build_strand(seq, "A", 1)
    lines.extend(strand1_lines)
    lines.append("TER")
    strand2_lines, _ = build_strand(comp_seq, "B", len(seq) + 1, is_complementary=True)
    lines.extend(strand2_lines)
    lines.append("TER")
    lines.append("END")
    Path(out_path).write_text("\n".join(lines) + "\n")
    return len(seq)


def main():
    out_dir = Path("data/dna_templates")
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(TARGETS.keys())
    for name in targets:
        seq = TARGETS[name]
        out_path = out_dir / f"{name}.pdb"
        n = generate_dna_pdb(name, seq, out_path)
        print(f"{name}: {seq} ({n}bp) -> {out_path}")


if __name__ == "__main__":
    main()
