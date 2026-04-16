"""Pipeline orchestrator: run full analysis per DNA target."""
from __future__ import annotations
import sys
from pathlib import Path
from analysis.normalize import (
    load_candidates, deduplicate, CandidateBinder, DNATarget, TARGET_SHORTHANDS,
)
from analysis.quality import apply_quality_gate, check_batch_diversity
from analysis.similarity import compute_sequence_identity_matrix, compute_structural_similarity_matrix
from analysis.redundancy import cluster_candidates
from analysis.modules import (
    align_representatives, compute_conservation_scores, identify_modules,
    identify_structural_modules,
)
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
    print(f"\n[{shorthand}] Starting analysis of {len(candidates)} candidates...", file=sys.stderr)

    unique = deduplicate(candidates)
    target.unique_count = len(unique)
    print(f"[{shorthand}] After dedup: {len(unique)}", file=sys.stderr)

    if not skip_esmfold:
        from analysis.predict import predict_batch
        struct_dir = output_dir / "structures" / shorthand
        print(f"[{shorthand}] Running ESMFold API predictions to {struct_dir}...", file=sys.stderr)
        unique = predict_batch(unique, struct_dir)
        n_with_pdb = sum(1 for c in unique if c.pdb_path)
        print(f"[{shorthand}] ESMFold done: {n_with_pdb}/{len(unique)} structures", file=sys.stderr)

    filtered = apply_quality_gate(unique)
    target.filtered_count = len(filtered)
    print(f"[{shorthand}] After quality gate: {len(filtered)}", file=sys.stderr)

    if len(filtered) < 2:
        return {
            "target": target,
            "candidates": filtered,
            "clusters": [],
            "modules": [],
            "structural_modules": [],
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
    print(f"[{shorthand}] Clusters: {len(clusters)}, Independent: {len(reps)}", file=sys.stderr)

    # Sequence-based module identification
    modules = []
    if len(reps) >= 2:
        alignment = align_representatives(reps)
        conservation = compute_conservation_scores(alignment)
        modules = identify_modules(
            conservation, alignment, reps, target_seq,
            min_length=10, min_conservation=0.4, min_occurrences=min(3, len(reps)),
        )
    print(f"[{shorthand}] Sequence modules: {len(modules)}", file=sys.stderr)

    # Structural module identification (TM-score based)
    structural_modules = []
    has_structures = any(c.pdb_path and Path(c.pdb_path).exists() for c in filtered)
    if has_structures and len(filtered) >= 3:
        print(f"[{shorthand}] Computing structural similarity matrix ({len(filtered)}x{len(filtered)})...", file=sys.stderr)
        tm_matrix = compute_structural_similarity_matrix(filtered)
        for threshold in [0.7, 0.6, 0.5]:
            structural_modules = identify_structural_modules(
                filtered, tm_matrix, target_seq,
                tm_threshold=threshold, min_cluster_size=3,
            )
            if structural_modules:
                print(f"[{shorthand}] Found {len(structural_modules)} structural families at TM>{threshold}", file=sys.stderr)
                break
        if not structural_modules:
            print(f"[{shorthand}] No structural families found (all designs structurally distinct)", file=sys.stderr)
    elif has_structures:
        print(f"[{shorthand}] Too few candidates for structural clustering (<3)", file=sys.stderr)
    else:
        print(f"[{shorthand}] No PDB structures available — skipping structural analysis", file=sys.stderr)

    all_modules = modules
    assessments = [assess_modularity(m, filtered) for m in all_modules]

    wiki_page = generate_synthesis_page(
        target, filtered, clusters, modules, assessments,
        structural_modules=structural_modules,
    )
    page_path = output_dir / "wiki" / f"syntheses/{shorthand.lower()}-binder-analysis.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(wiki_page)

    diversity = check_batch_diversity(filtered)

    return {
        "target": target,
        "candidates": filtered,
        "clusters": clusters,
        "modules": modules,
        "structural_modules": structural_modules,
        "assessments": assessments,
        "wiki_page": str(page_path),
        "diversity": diversity,
    }
