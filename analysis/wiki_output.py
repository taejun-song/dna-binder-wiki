"""Step 9: Generate wiki pages following CLAUDE.md conventions."""
from __future__ import annotations
from datetime import date
from analysis.normalize import CandidateBinder, DNATarget, TARGET_SHORTHANDS
from analysis.redundancy import RedundancyCluster
from analysis.modules import DNARecognitionModule, StructuralModule
from analysis.modularity import ModularityAssessment


def generate_synthesis_page(
    target: DNATarget,
    candidates: list[CandidateBinder],
    clusters: list[RedundancyCluster],
    modules: list[DNARecognitionModule],
    assessments: list[ModularityAssessment],
    structural_modules: list[StructuralModule] | None = None,
) -> str:
    today = date.today().isoformat()
    slug = target.shorthand.lower()
    filtered = [c for c in candidates if c.passes_quality]
    reps = [c for c in filtered if c.cluster_role == "representative"]

    lines = [
        "---",
        "type: synthesis",
        f'title: "{target.shorthand} DNA Binder Modularity Analysis"',
        f"created: {today}",
        f"updated: {today}",
        "sources:",
        '  - "[[rfd3-genome-editing-binders]]"',
        "tags: [dna-binding, modularity-analysis, protein-design]",
        "aliases: []",
        "---",
        "",
        f"# {target.shorthand} DNA Binder Modularity Analysis",
        "",
        f"Cross-design analysis of {len(candidates)} RFdiffusion3-generated binders targeting {target.sequence}, "
        f"testing the hypothesis that independently generated designs converge on reusable DNA-recognition modules.",
        "",
        "## Candidate Summary",
        "",
        f"- **Target DNA**: `{target.sequence}`",
        f"- **Total candidates**: {target.candidate_count}",
        f"- **After deduplication**: {target.unique_count}",
        f"- **Passing quality gate**: {target.filtered_count}",
        f"- **Redundancy clusters**: {target.cluster_count}",
        f"- **Independent designs**: {target.independent_count}",
        "",
    ]

    if clusters:
        lines.append("## Redundancy Analysis")
        lines.append("")
        for cl in clusters:
            lines.append(f"### Cluster {cl.cluster_id}")
            lines.append(f"- **Type**: {cl.similarity_type}")
            lines.append(f"- **Representative**: {cl.representative}")
            lines.append(f"- **Members**: {', '.join(cl.members)}")
            lines.append(f"- **Max sequence identity**: {cl.max_seq_identity:.1%}")
            lines.append("")

    if modules:
        lines.append("## Identified Modules")
        lines.append("")
        for mod in modules:
            lines.append(f"### {mod.module_id}")
            lines.append(f"- **Residue range**: {mod.residue_range}")
            lines.append(f"- **Length**: {mod.length} residues")
            lines.append(f"- **Conservation score**: {mod.conservation_score:.2f}")
            lines.append(f"- **Occurrences**: {mod.occurrences} independent designs")
            lines.append(f"- **Confidence**: {mod.confidence}")
            if mod.conserved_residues:
                lines.append(f"- **Conserved residues**: {', '.join(mod.conserved_residues[:10])}")
            lines.append("")
    else:
        lines.append("## Module Identification")
        lines.append("")
        lines.append("No conserved DNA-recognition modules were identified meeting the convergence threshold. "
                     "This may indicate insufficient independent designs or diverse binding strategies for this target.")
        lines.append("")

    if assessments:
        lines.append("## Modularity Assessment")
        lines.append("")
        for a in assessments:
            lines.append(f"### {a.module.module_id}")
            lines.append(f"- **Transferability score**: {a.transferability_score:.2f}")
            lines.append(f"- **Independent scaffolds**: {a.independent_scaffolds}")
            lines.append(f"- **Sequence preserved**: {'yes' if a.sequence_preserved else 'no'}")
            lines.append(f"- **Base-reading residues**: {', '.join(a.base_reading_residues[:5])}")
            lines.append(f"- **Confidence**: {a.confidence}")
            lines.append("")
            lines.append("**Experimental recommendations**:")
            lines.append("")
            for rec in a.experimental_recommendations:
                lines.append(f"1. {rec}")
            lines.append("")

    if structural_modules:
        lines.append("## Structural Families (TM-score)")
        lines.append("")
        lines.append(f"Structural comparison of ESMFold-predicted folds reveals {len(structural_modules)} "
                     f"structural family(ies) among the {target.filtered_count} candidates.")
        lines.append("")
        for sm in structural_modules:
            lines.append(f"### {sm.module_id}")
            lines.append(f"- **Family size**: {sm.structural_family_size} designs")
            lines.append(f"- **Mean TM-score**: {sm.mean_tm_score:.3f}")
            lines.append(f"- **Representative**: {sm.representative}")
            lines.append(f"- **Members**: {', '.join(sm.members)}")
            lines.append(f"- **Confidence**: {sm.confidence}")
            lines.append("")
    elif any(c.pdb_path for c in candidates):
        lines.append("## Structural Families (TM-score)")
        lines.append("")
        lines.append("All designs are structurally distinct — no structural families were detected "
                     "at TM-score thresholds of 0.5, 0.6, or 0.7. RFdiffusion3 generates highly "
                     "diverse fold topologies for this target.")
        lines.append("")

    lines.append("## See also")
    lines.append("")
    lines.append("- [[rfdiffusion3]] — the model used to generate all designs")
    lines.append("- [[dna-binder-design-targets]] — overview of all genome editing targets")
    lines.append("- [[rfd3-genome-editing-binders]] — the source dataset")
    lines.append("")

    return "\n".join(lines)


def generate_log_entry(
    target: DNATarget,
    pages_created: list[str],
    pages_updated: list[str],
) -> str:
    today = date.today().isoformat()
    lines = [
        f"## [{today}] query+page | {target.shorthand} binder modularity analysis",
        "",
    ]
    for p in pages_created:
        lines.append(f"- created: {p}")
    for p in pages_updated:
        lines.append(f"- updated: {p}")
    lines.append("- index.md: regenerated")
    return "\n".join(lines)
