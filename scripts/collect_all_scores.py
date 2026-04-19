#!/usr/bin/env python3
"""Collect all individual RF3 scores from autoresearch experiment directories.

Scans analysis_output/autoresearch/*/exp*/rf3/results/ for summary_confidences
JSON files and writes a single TSV with per-design pTM and ipTM scores.

Output: analysis_output/autoresearch/all_individual_scores.tsv
"""
import json
import sys
from pathlib import Path

def main():
    base = Path("analysis_output/autoresearch")
    out_path = base / "all_individual_scores.tsv"
    count = 0
    with open(out_path, "w") as out:
        out.write("target\texperiment\tdesign\tptm\tiptm\tranking_score\n")
        for target_dir in sorted(base.iterdir()):
            if not target_dir.is_dir():
                continue
            target = target_dir.name
            for exp_dir in sorted(target_dir.iterdir()):
                if not exp_dir.is_dir():
                    continue
                exp = exp_dir.name
                rf3_results = exp_dir / "rf3" / "results"
                if not rf3_results.exists():
                    continue
                for summary in rf3_results.rglob("*summary_confidences*"):
                    try:
                        d = json.load(open(summary))
                        ptm = d.get("ptm", 0)
                        iptm = d.get("iptm", 0)
                        ranking = d.get("ranking_score", 0)
                        design = summary.parent.name
                        out.write(f"{target}\t{exp}\t{design}\t{ptm:.4f}\t{iptm:.4f}\t{ranking:.4f}\n")
                        count += 1
                    except Exception:
                        pass
    print(f"Collected {count} individual scores -> {out_path}")


if __name__ == "__main__":
    main()
