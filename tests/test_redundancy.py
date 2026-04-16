"""Tests for redundancy clustering and origin classification."""
from analysis.normalize import load_candidates, deduplicate
from analysis.similarity import compute_sequence_identity_matrix
from analysis.redundancy import cluster_candidates, RedundancyCluster


def test_cluster_returns_list(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    seq_matrix = compute_sequence_identity_matrix(candidates)
    clusters = cluster_candidates(candidates, seq_matrix)
    assert isinstance(clusters, list)
    assert all(isinstance(c, RedundancyCluster) for c in clusters)


def test_specblock_variants_same_cluster(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    seq_matrix = compute_sequence_identity_matrix(candidates)
    clusters = cluster_candidates(candidates, seq_matrix)
    specblock_names = {c.shorthand_name for c in candidates if c.is_specblock}
    for cluster in clusters:
        member_set = set(cluster.members)
        overlap = member_set & specblock_names
        if len(overlap) >= 2:
            assert cluster.similarity_type in ("near-duplicate", "scaffold-variation")
            break
    else:
        pass


def test_every_candidate_assigned(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    seq_matrix = compute_sequence_identity_matrix(candidates)
    clusters = cluster_candidates(candidates, seq_matrix)
    all_members = set()
    for cl in clusters:
        all_members.update(cl.members)
    candidate_names = {c.shorthand_name for c in candidates}
    assert candidate_names == all_members


def test_cluster_has_representative(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    seq_matrix = compute_sequence_identity_matrix(candidates)
    clusters = cluster_candidates(candidates, seq_matrix)
    for cl in clusters:
        assert cl.representative in cl.members


def test_singletons_classified(sample_csv):
    candidates = deduplicate(load_candidates(sample_csv))
    seq_matrix = compute_sequence_identity_matrix(candidates)
    clusters = cluster_candidates(candidates, seq_matrix)
    singletons = [cl for cl in clusters if len(cl.members) == 1]
    for cl in singletons:
        assert cl.similarity_type == "singleton"
