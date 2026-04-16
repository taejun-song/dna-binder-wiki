"""Step 3: Quality gate filtering by pLDDT and sequence plausibility."""
from __future__ import annotations
from analysis.normalize import CandidateBinder

PLDDT_THRESHOLD = 0.70
MIN_LENGTH = 50
MAX_LENGTH = 500
STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")


def apply_quality_gate(candidates: list[CandidateBinder], plddt_threshold: float = PLDDT_THRESHOLD) -> list[CandidateBinder]:
    passed = []
    for c in candidates:
        if not _sequence_plausible(c):
            c.passes_quality = False
            continue
        if c.plddt_global is not None and c.plddt_global < plddt_threshold:
            c.passes_quality = False
            continue
        c.passes_quality = True
        passed.append(c)
    return passed


def _sequence_plausible(c: CandidateBinder) -> bool:
    if c.length < MIN_LENGTH or c.length > MAX_LENGTH:
        return False
    non_standard = set(c.sequence) - STANDARD_AA
    if non_standard:
        return False
    return True


def check_batch_diversity(candidates: list[CandidateBinder]) -> dict:
    batches: dict[str, int] = {}
    for c in candidates:
        parts = c.design_name.split("_")
        batch_key = "_".join(parts[:3]) if len(parts) >= 3 else c.design_name
        batches[batch_key] = batches.get(batch_key, 0) + 1
    return {
        "total_candidates": len(candidates),
        "unique_batches": len(batches),
        "batch_distribution": batches,
        "diverse": len(batches) > 1,
    }
