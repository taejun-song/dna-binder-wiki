"""Step 4: Pairwise sequence and structural similarity computation."""
from __future__ import annotations
import numpy as np
from Bio import Align
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
