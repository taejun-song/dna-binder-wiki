#!/usr/bin/env python3
"""Update all_candidates_full.csv with Phase 4 data and create top-10 CSV."""
import csv
import gzip
import json
from collections import OrderedDict
from pathlib import Path

AA3TO1 = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
    "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
    "TRP": "W", "TYR": "Y",
}
TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}
FIELDS = ["target", "dna_sequence", "source", "design_name", "ptm", "iptm",
          "ranking_score", "length", "parameters", "sequence"]


def extract_seq(cif_path):
    residues = OrderedDict()
    opener = gzip.open if str(cif_path).endswith(".gz") else open
    with opener(cif_path, "rt") as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            parts = line.split()
            if len(parts) >= 12 and parts[2] == "CA" and parts[4] in AA3TO1:
                key = (parts[5], parts[7])
                if key not in residues:
                    residues[key] = AA3TO1[parts[4]]
    return "".join(residues.values())


def collect_phase4():
    rows = []
    base = Path("analysis_output/autoresearch_phase4")
    if not base.exists():
        return rows
    for td in sorted(base.iterdir()):
        if not td.is_dir():
            continue
        target = td.name
        for ed in sorted(td.iterdir()):
            if not ed.is_dir():
                continue
            exp = ed.name
            cp = ed / "config.json"
            params = exp
            if cp.exists():
                try:
                    cfg = json.load(open(cp))
                    d = cfg.get("design", {})
                    c = d.get("contig", "")
                    lp = c.split(",")[-1] if ",/" in c else ""
                    params = "P4 L=" + lp if lp else "P4 " + exp
                except Exception:
                    pass
            rf3r = ed / "rf3" / "results"
            if not rf3r.exists():
                continue
            cd = ed / "rfd3_output"
            for s in rf3r.rglob("*summary_confidences*"):
                try:
                    dn = s.parent.name
                    if dn.startswith("seed-"):
                        continue
                    data = json.load(open(s))
                    seq = ""
                    if cd.exists():
                        for cf in cd.glob("*" + dn + "*.cif.gz"):
                            seq = extract_seq(cf)
                            if seq:
                                break
                    rows.append({
                        "target": target,
                        "dna_sequence": TARGETS.get(target, ""),
                        "source": "Phase4",
                        "design_name": "p4/" + exp + "/" + dn,
                        "ptm": round(data.get("ptm", 0), 4),
                        "iptm": round(data.get("iptm", 0), 4),
                        "ranking_score": round(data.get("ranking_score", 0), 4),
                        "length": len(seq),
                        "parameters": params,
                        "sequence": seq,
                    })
                except Exception:
                    pass
    return rows


def main():
    p4_rows = collect_phase4()
    print(f"Phase 4 scores: {len(p4_rows)}")

    existing = []
    full_csv = Path("analysis_output/all_candidates_full.csv")
    with open(full_csv) as f:
        for row in csv.DictReader(f):
            if row["source"] != "Phase4":
                existing.append(row)
    all_rows = existing + p4_rows
    all_rows.sort(key=lambda r: -float(r["iptm"]))

    with open(full_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"Updated CSV: {len(all_rows)} rows")

    # Top 10 per target per method
    top10 = []
    for t in sorted(TARGETS):
        for src in ["Baker Lab", "Overnight", "AutoRes", "Phase4"]:
            cands = sorted(
                [r for r in all_rows if r["target"] == t and r["source"] == src],
                key=lambda r: -float(r["iptm"]),
            )
            for i, r in enumerate(cands[:10], 1):
                top10.append(dict(r, rank=i))

    with open("analysis_output/top10_per_target_method.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank"] + FIELDS)
        w.writeheader()
        w.writerows(top10)
    print(f"Top-10 CSV: {len(top10)} rows")

    # Summary
    print()
    header = f"{'Target':12s} {'Baker':>8s} {'Overnight':>10s} {'AutoRes':>8s} {'Phase4':>8s}"
    print(header)
    print("-" * len(header))
    for t in sorted(TARGETS):
        vals = []
        for src in ["Baker Lab", "Overnight", "AutoRes", "Phase4"]:
            cands = [float(r["iptm"]) for r in all_rows if r["target"] == t and r["source"] == src]
            best = max(cands) if cands else 0
            vals.append(best)
        line = f"{t:12s}"
        for v in vals:
            if v > 0:
                line += f" {v:8.4f}"
            else:
                line += f" {'--':>8s}"
        print(line)


if __name__ == "__main__":
    main()
