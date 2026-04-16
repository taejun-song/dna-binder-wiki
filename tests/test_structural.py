"""Tests for structural similarity and structural module detection."""
import pytest
import tempfile
from pathlib import Path
from analysis.similarity import compute_structural_similarity_matrix, parse_pdb_coords
from analysis.modules import identify_structural_modules, StructuralModule
from analysis.normalize import CandidateBinder


def _make_pdb_line(serial, name, resname, chain, resseq, x, y, z, bfactor):
    # PDB format: columns 1-6 record, 7-11 serial, 13-16 name, 18-20 resname,
    # 22 chain, 23-26 resseq, 31-38 x, 39-46 y, 47-54 z, 55-60 occ, 61-66 bfactor
    return f"ATOM  {serial:5d} {name:<4s} {resname:>3s} {chain}{resseq:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{bfactor:6.2f}"


def _make_pdb(tmp: Path, name: str, offset: float = 0.0) -> str:
    pdb_path = tmp / f"{name}.pdb"
    lines = [
        _make_pdb_line(1, "N",  "ALA", "A", 1, 1.0+offset, 2.0, 3.0, 80.0),
        _make_pdb_line(2, "CA", "ALA", "A", 1, 2.5+offset, 2.0, 3.0, 80.0),
        _make_pdb_line(3, "C",  "ALA", "A", 1, 4.0+offset, 2.0, 3.0, 80.0),
        _make_pdb_line(4, "N",  "ALA", "A", 2, 5.0+offset, 2.0, 3.0, 85.0),
        _make_pdb_line(5, "CA", "ALA", "A", 2, 6.5+offset, 2.0, 3.0, 85.0),
        _make_pdb_line(6, "C",  "ALA", "A", 2, 8.0+offset, 2.0, 3.0, 85.0),
        "END",
    ]
    pdb_path.write_text("\n".join(lines))
    return str(pdb_path)


def test_parse_pdb_coords():
    with tempfile.TemporaryDirectory() as tmp:
        pdb_path = _make_pdb(Path(tmp), "test")
        coords = parse_pdb_coords(pdb_path)
        assert coords is not None
        assert len(coords) == 2  # 2 CA atoms


def test_structural_similarity_matrix_shape():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        candidates = []
        for i in range(3):
            c = CandidateBinder(
                design_name=f"d{i}", shorthand_name=f"s{i}",
                sequence="AA", target_dna="ACGT",
            )
            c.pdb_path = _make_pdb(tmp, f"s{i}", offset=i * 0.1)
            candidates.append(c)
        matrix = compute_structural_similarity_matrix(candidates)
        assert matrix.shape == (3, 3)


def test_structural_similarity_self_is_one():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        c = CandidateBinder(
            design_name="d0", shorthand_name="s0",
            sequence="AA", target_dna="ACGT",
        )
        c.pdb_path = _make_pdb(tmp, "s0")
        matrix = compute_structural_similarity_matrix([c])
        assert abs(matrix[0, 0] - 1.0) < 0.01


def test_similar_structures_high_tm():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        candidates = []
        for i in range(2):
            c = CandidateBinder(
                design_name=f"d{i}", shorthand_name=f"s{i}",
                sequence="AA", target_dna="ACGT",
            )
            c.pdb_path = _make_pdb(tmp, f"s{i}", offset=i * 0.01)
            candidates.append(c)
        matrix = compute_structural_similarity_matrix(candidates)
        assert matrix[0, 1] > 0.5
