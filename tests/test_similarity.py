"""Tests for pairwise sequence similarity computation."""
from analysis.normalize import load_candidates, deduplicate
from analysis.similarity import compute_sequence_identity_matrix


def test_identity_matrix_shape(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    matrix = compute_sequence_identity_matrix(candidates)
    n = len(candidates)
    assert matrix.shape == (n, n)


def test_identity_matrix_diagonal_is_one(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    matrix = compute_sequence_identity_matrix(candidates)
    for i in range(len(candidates)):
        assert abs(matrix[i, i] - 1.0) < 0.01


def test_identity_matrix_symmetric(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    matrix = compute_sequence_identity_matrix(candidates)
    n = len(candidates)
    for i in range(n):
        for j in range(i + 1, n):
            assert abs(matrix[i, j] - matrix[j, i]) < 0.01


def test_specblock_variants_high_similarity(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    specblocks = [i for i, c in enumerate(candidates) if c.is_specblock]
    if len(specblocks) >= 2:
        i, j = specblocks[0], specblocks[1]
        matrix = compute_sequence_identity_matrix(candidates)
        assert matrix[i, j] > 0.5


def test_different_targets_low_similarity(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    pnrp1_idx = [i for i, c in enumerate(candidates) if c.target_dna == "TGAGGAGAGGAG"]
    cag_idx = [i for i, c in enumerate(candidates) if c.target_dna == "CAGCAGCAGCAG"]
    if pnrp1_idx and cag_idx:
        matrix = compute_sequence_identity_matrix(candidates)
        assert matrix[pnrp1_idx[0], cag_idx[0]] < 0.9
