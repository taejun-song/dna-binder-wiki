"""Step 7: DNA-recognition module identification via sequence + structural conservation."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from Bio import AlignIO
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from analysis.normalize import CandidateBinder


@dataclass
class DNARecognitionModule:
    module_id: str
    target_dna: str
    residue_range: str = ""
    length: int = 0
    conserved_residues: list[str] = field(default_factory=list)
    structural_description: str = ""
    conservation_score: float = 0.0
    structural_rmsd: float | None = None
    plddt_mean: float = 0.0
    occurrences: int = 0
    scaffold_ids: list[str] = field(default_factory=list)
    confidence: str = "low"


def align_representatives(candidates: list[CandidateBinder]) -> list[str]:
    if len(candidates) < 2:
        return [c.sequence for c in candidates]
    try:
        return _align_with_muscle(candidates)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return _simple_pad_alignment(candidates)


def _align_with_muscle(candidates: list[CandidateBinder]) -> list[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        for i, c in enumerate(candidates):
            f.write(f">{c.shorthand_name}\n{c.sequence}\n")
        infile = f.name
    outfile = infile + ".aligned"
    try:
        subprocess.run(
            ["muscle", "-align", infile, "-output", outfile],
            check=True, capture_output=True, timeout=60,
        )
        alignment = AlignIO.read(outfile, "fasta")
        name_to_seq = {rec.id: str(rec.seq) for rec in alignment}
        return [name_to_seq.get(c.shorthand_name, c.sequence) for c in candidates]
    finally:
        Path(infile).unlink(missing_ok=True)
        Path(outfile).unlink(missing_ok=True)


def _simple_pad_alignment(candidates: list[CandidateBinder]) -> list[str]:
    max_len = max(len(c.sequence) for c in candidates)
    return [c.sequence.ljust(max_len, "-") for c in candidates]


def compute_conservation_scores(alignment: list[str]) -> list[float]:
    if not alignment:
        return []
    aln_len = len(alignment[0])
    n_seqs = len(alignment)
    scores = []
    for col in range(aln_len):
        residues = [seq[col] for seq in alignment if col < len(seq)]
        non_gap = [r for r in residues if r != "-"]
        if not non_gap:
            scores.append(0.0)
            continue
        counts = Counter(non_gap)
        most_common_count = counts.most_common(1)[0][1]
        scores.append(most_common_count / n_seqs)
    return scores


def identify_modules(
    conservation_scores: list[float],
    alignment: list[str],
    candidates: list[CandidateBinder],
    target_dna: str,
    min_length: int = 15,
    min_conservation: float = 0.6,
    min_occurrences: int = 3,
) -> list[DNARecognitionModule]:
    n_seqs = len(alignment)
    if n_seqs < min_occurrences:
        min_occurrences = max(2, n_seqs)

    regions = _find_conserved_regions(conservation_scores, min_length, min_conservation)
    modules = []
    for idx, (start, end) in enumerate(regions):
        region_scores = conservation_scores[start:end]
        avg_conservation = sum(region_scores) / len(region_scores) if region_scores else 0.0
        occurrences = 0
        scaffold_ids = []
        conserved_residues = []
        for i, seq in enumerate(alignment):
            region_seq = seq[start:end].replace("-", "")
            if len(region_seq) >= min_length * 0.5:
                occurrences += 1
                scaffold_ids.append(candidates[i].shorthand_name)
        for col in range(start, end):
            if conservation_scores[col] >= 0.7:
                non_gap = [seq[col] for seq in alignment if seq[col] != "-"]
                if non_gap:
                    mc = Counter(non_gap).most_common(1)[0]
                    conserved_residues.append(f"{mc[0]}{col + 1}")

        if occurrences >= min_occurrences:
            module = DNARecognitionModule(
                module_id=f"{target_dna[:8]}_MOD{idx + 1:02d}",
                target_dna=target_dna,
                residue_range=f"{start + 1}-{end}",
                length=end - start,
                conserved_residues=conserved_residues,
                conservation_score=avg_conservation,
                occurrences=occurrences,
                scaffold_ids=scaffold_ids,
                confidence="medium" if avg_conservation > 0.7 else "low",
            )
            modules.append(module)
    return modules


def _find_conserved_regions(
    scores: list[float], min_length: int, min_conservation: float
) -> list[tuple[int, int]]:
    regions = []
    in_region = False
    start = 0
    for i, score in enumerate(scores):
        if score >= min_conservation:
            if not in_region:
                start = i
                in_region = True
        else:
            if in_region:
                if i - start >= min_length:
                    regions.append((start, i))
                in_region = False
    if in_region and len(scores) - start >= min_length:
        regions.append((start, len(scores)))
    return regions


@dataclass
class StructuralModule:
    module_id: str
    target_dna: str
    mean_tm_score: float = 0.0
    structural_family_size: int = 0
    members: list[str] = field(default_factory=list)
    representative: str = ""
    confidence: str = "low"


def identify_structural_modules(
    candidates: list[CandidateBinder],
    tm_matrix: np.ndarray,
    target_dna: str,
    tm_threshold: float = 0.5,
    min_cluster_size: int = 3,
) -> list[StructuralModule]:
    n = len(candidates)
    assigned = [False] * n
    modules: list[StructuralModule] = []
    mod_counter = 0

    for i in range(n):
        if assigned[i]:
            continue
        cluster_idx = [i]
        assigned[i] = True
        for j in range(i + 1, n):
            if assigned[j]:
                continue
            if tm_matrix[i, j] >= tm_threshold:
                all_above = all(
                    tm_matrix[k, j] >= tm_threshold * 0.8
                    for k in cluster_idx
                )
                if all_above:
                    cluster_idx.append(j)
                    assigned[j] = True

        if len(cluster_idx) < min_cluster_size:
            continue

        mod_counter += 1
        member_names = [candidates[idx].shorthand_name for idx in cluster_idx]
        tm_scores = []
        for a in range(len(cluster_idx)):
            for b in range(a + 1, len(cluster_idx)):
                tm_scores.append(tm_matrix[cluster_idx[a], cluster_idx[b]])
        mean_tm = float(np.mean(tm_scores)) if tm_scores else 0.0

        best_idx = cluster_idx[0]
        best_score = 0.0
        for idx in cluster_idx:
            avg = float(np.mean([tm_matrix[idx, j] for j in cluster_idx if j != idx])) if len(cluster_idx) > 1 else 1.0
            if avg > best_score:
                best_score = avg
                best_idx = idx

        confidence = "high" if mean_tm > 0.7 else "medium" if mean_tm > 0.5 else "low"
        modules.append(StructuralModule(
            module_id=f"{target_dna[:8]}_STMOD{mod_counter:02d}",
            target_dna=target_dna,
            mean_tm_score=mean_tm,
            structural_family_size=len(cluster_idx),
            members=member_names,
            representative=candidates[best_idx].shorthand_name,
            confidence=confidence,
        ))

    return modules
