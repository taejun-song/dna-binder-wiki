from analysis.normalize import load_candidates, deduplicate, CandidateBinder, DNATarget


def test_load_candidates_returns_list(sample_csv):
    candidates = load_candidates(sample_csv)
    assert isinstance(candidates, list)
    assert len(candidates) == 10
    assert all(isinstance(c, CandidateBinder) for c in candidates)


def test_load_candidates_parses_fields(sample_csv):
    candidates = load_candidates(sample_csv)
    c = candidates[0]
    assert c.shorthand_name == "PNRP1_design21"
    assert c.target_dna == "TGAGGAGAGGAG"
    assert len(c.sequence) > 50
    assert c.design_name.startswith("TGAGGAGAGGAG")


def test_load_candidates_detects_specblock(sample_csv):
    candidates = load_candidates(sample_csv)
    specblocks = [c for c in candidates if c.is_specblock]
    assert len(specblocks) == 2
    for sb in specblocks:
        assert "specblock" in sb.shorthand_name


def test_deduplicate_removes_exact_duplicates(sample_csv):
    candidates = load_candidates(sample_csv)
    unique = deduplicate(candidates)
    assert len(unique) == 9
    seqs = [c.sequence for c in unique]
    assert len(seqs) == len(set(seqs))


def test_deduplicate_preserves_metadata(sample_csv):
    candidates = load_candidates(sample_csv)
    unique = deduplicate(candidates)
    names = {c.shorthand_name for c in unique}
    assert "PNRP1_design21" in names


def test_candidate_length_computed(sample_csv):
    candidates = load_candidates(sample_csv)
    for c in candidates:
        assert c.length == len(c.sequence)


def test_group_by_target(sample_csv):
    candidates = load_candidates(sample_csv)
    unique = deduplicate(candidates)
    targets = {}
    for c in unique:
        targets.setdefault(c.target_dna, []).append(c)
    assert "TGAGGAGAGGAG" in targets
    assert "CAGCAGCAGCAG" in targets
    assert len(targets["TGAGGAGAGGAG"]) == 5
