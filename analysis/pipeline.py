"""Pipeline orchestrator: run full analysis per DNA target."""
from __future__ import annotations
from pathlib import Path
from analysis.normalize import (
    load_candidates, deduplicate, CandidateBinder, DNATarget, TARGET_SHORTHANDS,
)
from analysis.quality import apply_quality_gate, check_batch_diversity
from analysis.similarity import compute_sequence_identity_matrix
from analysis.redundancy import cluster_candidates
from analysis.modules import align_representatives, compute_conservation_scores, identify_modules
from analysis.modularity import assess_modularity
from analysis.wiki_output import generate_synthesis_page, generate_log_entry


def run_pipeline(
    csv_path: str | Path,
    target_dna: str | None = None,
    output_dir: str | Path = "analysis_output",
    skip_esmfold: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_candidates = load_candidates(csv_path)

    if target_dna:
        targets = {target_dna}
    else:
        targets = {c.target_dna for c in all_candidates}

    results = {}
    for target_seq in sorted(targets):
        shorthand = TARGET_SHORTHANDS.get(target_seq, target_seq[:8])
        target_candidates = [c for c in all_candidates if c.target_dna == target_seq]
        result = _analyze_target(target_seq, shorthand, target_candidates, output_dir, skip_esmfold)
        results[target_seq] = result

    return results


def _analyze_target(
    target_seq: str,
    shorthand: str,
    candidates: list[CandidateBinder],
    output_dir: Path,
    skip_esmfold: bool,
) -> dict:
    target = DNATarget(sequence=target_seq, shorthand=shorthand)
    target.candidate_count = len(candidates)

    unique = deduplicate(candidates)
    target.unique_count = len(unique)

    if not skip_esmfold:
        try:
            from analysis.predict import predict_batch
            struct_dir = output_dir / "structures" / shorthand
            unique = predict_batch(unique, struct_dir)
        except ImportError:
            pass

    filtered = apply_quality_gate(unique)
    target.filtered_count = len(filtered)

    if len(filtered) < 2:
        return {
            "target": target,
            "candidates": filtered,
            "clusters": [],
            "modules": [],
            "assessments": [],
            "wiki_page": None,
            "diversity": check_batch_diversity(filtered),
        }

    seq_matrix = compute_sequence_identity_matrix(filtered)
    clusters = cluster_candidates(filtered, seq_matrix)
    target.cluster_count = len(clusters)

    reps = []
    seen = set()
    for cl in clusters:
        if cl.representative not in seen:
            seen.add(cl.representative)
            for c in filtered:
                if c.shorthand_name == cl.representative:
                    reps.append(c)
                    break
    target.independent_count = len(reps)

    modules = []
    assessments = []
    if len(reps) >= 2:
        alignment = align_representatives(reps)
        conservation = compute_conservation_scores(alignment)
        modules = identify_modules(
            conservation, alignment, reps, target_seq,
            min_length=10, min_conservation=0.4, min_occurrences=min(3, len(reps)),
        )
        assessments = [assess_modularity(m, filtered) for m in modules]

    wiki_page = generate_synthesis_page(target, filtered, clusters, modules, assessments)
    page_path = output_dir / "wiki" / f"syntheses/{shorthand.lower()}-binder-analysis.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(wiki_page)

    diversity = check_batch_diversity(filtered)

    return {
        "target": target,
        "candidates": filtered,
        "clusters": clusters,
        "modules": modules,
        "assessments": assessments,
        "wiki_page": str(page_path),
        "diversity": diversity,
    }
