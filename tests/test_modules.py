"""Tests for DNA-recognition module identification."""
from analysis.normalize import load_candidates, deduplicate
from analysis.similarity import compute_sequence_identity_matrix
from analysis.redundancy import cluster_candidates
from analysis.modules import (
    align_representatives,
    compute_conservation_scores,
    identify_modules,
    DNARecognitionModule,
)


def _get_pnrp1_representatives(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    pnrp1 = [c for c in candidates if c.target_dna == "TGAGGAGAGGAG"]
    seq_matrix = compute_sequence_identity_matrix(pnrp1)
    clusters = cluster_candidates(pnrp1, seq_matrix)
    reps = []
    seen = set()
    for cl in clusters:
        if cl.representative not in seen:
            seen.add(cl.representative)
            for c in pnrp1:
                if c.shorthand_name == cl.representative:
                    reps.append(c)
                    break
    return reps


def test_align_representatives_returns_alignment(sample_csv):
    reps = _get_pnrp1_representatives(sample_csv)
    if len(reps) < 2:
        return
    alignment = align_representatives(reps)
    assert alignment is not None
    assert len(alignment) == len(reps)


def test_conservation_scores_length(sample_csv):
    reps = _get_pnrp1_representatives(sample_csv)
    if len(reps) < 2:
        return
    alignment = align_representatives(reps)
    scores = compute_conservation_scores(alignment)
    assert len(scores) > 0
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_identify_modules_returns_list(sample_csv):
    reps = _get_pnrp1_representatives(sample_csv)
    if len(reps) < 3:
        return
    alignment = align_representatives(reps)
    scores = compute_conservation_scores(alignment)
    modules = identify_modules(scores, alignment, reps, "TGAGGAGAGGAG", min_length=5, min_conservation=0.3, min_occurrences=2)
    assert isinstance(modules, list)
    for m in modules:
        assert isinstance(m, DNARecognitionModule)


def test_module_has_required_fields(sample_csv):
    reps = _get_pnrp1_representatives(sample_csv)
    if len(reps) < 3:
        return
    alignment = align_representatives(reps)
    scores = compute_conservation_scores(alignment)
    modules = identify_modules(scores, alignment, reps, "TGAGGAGAGGAG", min_length=5, min_conservation=0.3, min_occurrences=2)
    for m in modules:
        assert m.module_id
        assert m.target_dna == "TGAGGAGAGGAG"
        assert m.length > 0
        assert m.conservation_score > 0.0
        assert m.occurrences >= 2
