"""Step 4: Pairwise sequence and structural similarity computation."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from Bio import Align
from Bio.PDB import PDBParser
from analysis.normalize import CandidateBinder


def _pairwise_identity(seq1: str, seq2: str) -> float:
    if seq1 == seq2:
        return 1.0
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 1
    aligner.mismatch_score = 0
    aligner.open_gap_score = -2
    aligner.extend_gap_score = -0.5
    alignments = aligner.align(seq1, seq2)
    if not alignments:
        return 0.0
    best = alignments[0]
    matches = sum(1 for a, b in zip(best[0], best[1]) if a == b and a != "-")
    alignment_len = max(len(seq1), len(seq2))
    return matches / alignment_len if alignment_len > 0 else 0.0


def compute_sequence_identity_matrix(candidates: list[CandidateBinder]) -> np.ndarray:
    n = len(candidates)
    matrix = np.zeros((n, n))
    for i in range(n):
        matrix[i, i] = 1.0
        for j in range(i + 1, n):
            identity = _pairwise_identity(candidates[i].sequence, candidates[j].sequence)
            matrix[i, j] = identity
            matrix[j, i] = identity
    return matrix


def parse_pdb_coords(pdb_path: str) -> np.ndarray | None:
    coords = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append([x, y, z])
                except (ValueError, IndexError):
                    continue
    return np.array(coords) if coords else None


def _tm_score(coords1: np.ndarray, coords2: np.ndarray) -> float:
    try:
        import tmtools
        result = tmtools.tm_align(coords1, coords2, coords1, coords2)
        return float(result.tm_norm_chain1)
    except ImportError:
        return _simple_tm_score(coords1, coords2)


def _simple_tm_score(coords1: np.ndarray, coords2: np.ndarray) -> float:
    n = min(len(coords1), len(coords2))
    if n == 0:
        return 0.0
    c1 = coords1[:n] - coords1[:n].mean(axis=0)
    c2 = coords2[:n] - coords2[:n].mean(axis=0)
    H = c1.T @ c2
    U, S, Vt = np.linalg.svd(H)
    d = np.linalg.det(Vt.T @ U.T)
    sign_matrix = np.diag([1, 1, np.sign(d)])
    R = Vt.T @ sign_matrix @ U.T
    c2_rotated = (R @ c2.T).T
    dist_sq = np.sum((c1 - c2_rotated) ** 2, axis=1)
    d0 = 1.24 * (n - 15) ** (1.0 / 3.0) - 1.8 if n > 15 else 0.5
    d0 = max(d0, 0.5)
    tm = np.sum(1.0 / (1.0 + dist_sq / (d0 ** 2))) / n
    return float(tm)


def compute_structural_similarity_matrix(candidates: list[CandidateBinder]) -> np.ndarray:
    n = len(candidates)
    matrix = np.zeros((n, n))
    coords_cache: list[np.ndarray | None] = []
    for c in candidates:
        if c.pdb_path and Path(c.pdb_path).exists():
            coords_cache.append(parse_pdb_coords(c.pdb_path))
        else:
            coords_cache.append(None)
    for i in range(n):
        matrix[i, i] = 1.0
        if coords_cache[i] is None:
            continue
        for j in range(i + 1, n):
            if coords_cache[j] is None:
                continue
            score = _tm_score(coords_cache[i], coords_cache[j])
            matrix[i, j] = score
            matrix[j, i] = score
    return matrix
