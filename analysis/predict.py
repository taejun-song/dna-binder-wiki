"""Step 2: ESMFold structure prediction via API or local model."""
from __future__ import annotations
import time
from pathlib import Path
import requests
from analysis.normalize import CandidateBinder

ESMFOLD_API = "https://api.esmatlas.com/foldSequence/v1/pdb/"


def predict_structure_api(candidate: CandidateBinder, output_dir: Path) -> CandidateBinder:
    pdb_path = output_dir / f"{candidate.shorthand_name}.pdb"
    if pdb_path.exists():
        pdb_text = pdb_path.read_text()
    else:
        resp = requests.post(ESMFOLD_API, data=candidate.sequence, timeout=120)
        resp.raise_for_status()
        pdb_text = resp.text
        pdb_path.write_text(pdb_text)

    plddt = _extract_plddt(pdb_text)
    candidate.pdb_path = str(pdb_path)
    candidate.plddt_per_residue = plddt
    candidate.plddt_global = sum(plddt) / len(plddt) if plddt else 0.0
    return candidate


def predict_batch(candidates: list[CandidateBinder], output_dir: Path) -> list[CandidateBinder]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(candidates):
        pdb_path = output_dir / f"{c.shorthand_name}.pdb"
        if pdb_path.exists():
            pdb_text = pdb_path.read_text()
            plddt = _extract_plddt(pdb_text)
            c.pdb_path = str(pdb_path)
            c.plddt_per_residue = plddt
            c.plddt_global = sum(plddt) / len(plddt) if plddt else 0.0
            continue
        try:
            resp = requests.post(ESMFOLD_API, data=c.sequence, timeout=120)
            resp.raise_for_status()
            pdb_text = resp.text
            pdb_path.write_text(pdb_text)
            plddt = _extract_plddt(pdb_text)
            c.pdb_path = str(pdb_path)
            c.plddt_per_residue = plddt
            c.plddt_global = sum(plddt) / len(plddt) if plddt else 0.0
        except Exception as e:
            import sys
            print(f"  ESMFold API failed for {c.shorthand_name}: {e}", file=sys.stderr)
        if i < len(candidates) - 1:
            time.sleep(0.5)
    return candidates


def _extract_plddt(pdb_text: str) -> list[float]:
    plddt = []
    for line in pdb_text.split("\n"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                bfactor = float(line[60:66].strip())
                plddt.append(bfactor)
            except (ValueError, IndexError):
                continue
    return plddt
