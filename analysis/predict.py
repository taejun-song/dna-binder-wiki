"""Step 2: ESMFold structure prediction. Requires GPU — run on remote server."""
from __future__ import annotations
from pathlib import Path
from analysis.normalize import CandidateBinder


def predict_structure(candidate: CandidateBinder, output_dir: Path) -> CandidateBinder:
    """Predict structure for a single candidate using ESMFold.

    Requires: torch, esm (install with `uv add torch fair-esm`)
    Best run on GPU server (taejun@10.167.0.7).
    """
    import torch
    import esm

    model = esm.pretrained.esmfold_v1()
    model = model.eval()
    if torch.cuda.is_available():
        model = model.cuda()

    with torch.no_grad():
        output = model.infer_pdb(candidate.sequence)

    pdb_path = output_dir / f"{candidate.shorthand_name}.pdb"
    pdb_path.write_text(output)

    plddt_per_residue = _extract_plddt(output)
    candidate.pdb_path = str(pdb_path)
    candidate.plddt_per_residue = plddt_per_residue
    candidate.plddt_global = sum(plddt_per_residue) / len(plddt_per_residue) if plddt_per_residue else 0.0
    return candidate


def predict_batch(candidates: list[CandidateBinder], output_dir: Path) -> list[CandidateBinder]:
    """Predict structures for all candidates. Loads model once."""
    import torch
    import esm

    output_dir.mkdir(parents=True, exist_ok=True)
    model = esm.pretrained.esmfold_v1()
    model = model.eval()
    if torch.cuda.is_available():
        model = model.cuda()

    for c in candidates:
        pdb_path = output_dir / f"{c.shorthand_name}.pdb"
        if pdb_path.exists():
            pdb_text = pdb_path.read_text()
            plddt = _extract_plddt(pdb_text)
            c.pdb_path = str(pdb_path)
            c.plddt_per_residue = plddt
            c.plddt_global = sum(plddt) / len(plddt) if plddt else 0.0
            continue
        with torch.no_grad():
            pdb_text = model.infer_pdb(c.sequence)
        pdb_path.write_text(pdb_text)
        plddt = _extract_plddt(pdb_text)
        c.pdb_path = str(pdb_path)
        c.plddt_per_residue = plddt
        c.plddt_global = sum(plddt) / len(plddt) if plddt else 0.0
    return candidates


def _extract_plddt(pdb_text: str) -> list[float]:
    """Extract per-residue pLDDT from B-factor column of CA atoms."""
    plddt = []
    for line in pdb_text.split("\n"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                bfactor = float(line[60:66].strip())
                plddt.append(bfactor)
            except (ValueError, IndexError):
                continue
    return plddt
