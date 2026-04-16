"""Step 1: Load, normalize, and deduplicate RFD3 binder candidates."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

TARGET_SHORTHANDS = {
    "TGAGGAGAGGAG": "PNRP1",
    "CAGCAGCAGCAG": "CAG",
    "AGGGTTAGGGTT": "HSTELO",
    "GGGCTTGCGA": "OCT4pt2",
    "GGTGAAATGA": "OCT4pt1",
    "GGGGATTCCCCC": "NFKB",
    "GCTTAATTAGCG": "HD",
    "CGTATAAACG": "TATA",
    "CAGGCCGCAGG": "Dux4grna2",
}


@dataclass
class CandidateBinder:
    design_name: str
    shorthand_name: str
    sequence: str
    target_dna: str
    length: int = 0
    is_specblock: bool = False
    parent_design: str | None = None
    pdb_path: str | None = None
    plddt_global: float | None = None
    plddt_per_residue: list[float] = field(default_factory=list)
    passes_quality: bool = False
    binding_class: str | None = None
    candidate_contacts: list[int] = field(default_factory=list)
    cluster_id: str | None = None
    cluster_role: str | None = None
    module_region: tuple[int, int] | None = None
    confidence: str | None = None

    def __post_init__(self):
        self.length = len(self.sequence)
        self.is_specblock = "specblock" in self.design_name.lower() or "specblock" in self.shorthand_name.lower()


@dataclass
class DNATarget:
    sequence: str
    shorthand: str
    candidate_count: int = 0
    unique_count: int = 0
    filtered_count: int = 0
    cluster_count: int = 0
    independent_count: int = 0


def load_candidates(csv_path: str | Path) -> list[CandidateBinder]:
    df = pd.read_csv(csv_path)
    candidates = []
    for _, row in df.iterrows():
        c = CandidateBinder(
            design_name=row["design_name"],
            shorthand_name=row["shorthand_name"],
            sequence=row["amino acid sequence"],
            target_dna=row["on_target_seq"],
        )
        candidates.append(c)
    return candidates


def deduplicate(candidates: list[CandidateBinder]) -> list[CandidateBinder]:
    seen: dict[str, CandidateBinder] = {}
    for c in candidates:
        if c.sequence not in seen:
            seen[c.sequence] = c
    return list(seen.values())
