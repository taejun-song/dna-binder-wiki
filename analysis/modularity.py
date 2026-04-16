"""Step 8: Modularity and programmability assessment."""
from __future__ import annotations
from dataclasses import dataclass, field
from analysis.modules import DNARecognitionModule
from analysis.normalize import CandidateBinder


@dataclass
class ModularityAssessment:
    module: DNARecognitionModule
    independent_scaffolds: int = 0
    sequence_preserved: bool = False
    base_reading_residues: list[str] = field(default_factory=list)
    scaffold_anchoring_residues: list[str] = field(default_factory=list)
    transferability_score: float = 0.0
    confidence: str = "low"
    experimental_recommendations: list[str] = field(default_factory=list)


CHARGED_POLAR = set("RKHNQE")
HYDROPHOBIC = set("AVILMFYW")


def assess_modularity(
    module: DNARecognitionModule,
    candidates: list[CandidateBinder],
) -> ModularityAssessment:
    assessment = ModularityAssessment(module=module)
    assessment.independent_scaffolds = module.occurrences
    assessment.sequence_preserved = module.conservation_score > 0.6

    for res_str in module.conserved_residues:
        aa = res_str[0]
        if aa in CHARGED_POLAR:
            assessment.base_reading_residues.append(res_str)
        elif aa in HYDROPHOBIC:
            assessment.scaffold_anchoring_residues.append(res_str)

    score = 0.0
    if assessment.independent_scaffolds >= 3:
        score += 0.3
    if assessment.sequence_preserved:
        score += 0.3
    if len(assessment.base_reading_residues) >= 3:
        score += 0.2
    if module.conservation_score > 0.7:
        score += 0.2
    assessment.transferability_score = min(score, 1.0)

    if assessment.transferability_score >= 0.7:
        assessment.confidence = "high"
    elif assessment.transferability_score >= 0.4:
        assessment.confidence = "medium"
    else:
        assessment.confidence = "low"

    assessment.experimental_recommendations = _generate_recommendations(module, assessment)
    return assessment


def _generate_recommendations(
    module: DNARecognitionModule,
    assessment: ModularityAssessment,
) -> list[str]:
    recs = []
    recs.append(
        f"Transplant module (residues {module.residue_range}) onto a different scaffold "
        f"backbone and test DNA binding by yeast surface display."
    )
    recs.append(
        f"Perform alanine scanning of conserved base-reading residues "
        f"({', '.join(assessment.base_reading_residues[:5])}) to confirm their role in DNA recognition."
    )
    recs.append(
        f"Redesign the module for a related DNA sequence (e.g., single base mutation of {module.target_dna}) "
        f"and test for shifted specificity."
    )
    if assessment.independent_scaffolds >= 3:
        recs.append(
            f"Swap variable regions between the {assessment.independent_scaffolds} scaffolds "
            f"containing this module to test scaffold independence."
        )
    return recs
