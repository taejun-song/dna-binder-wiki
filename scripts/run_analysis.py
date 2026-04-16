#!/usr/bin/env python3
"""CLI entry point for DNA binder modularity analysis."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analysis.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Analyze RFD3 DNA binder candidates for modularity")
    parser.add_argument("--input", required=True, help="Path to CSV file with binder candidates")
    parser.add_argument("--target", default=None, help="Specific DNA target sequence to analyze")
    parser.add_argument("--all-targets", action="store_true", help="Analyze all targets in dataset")
    parser.add_argument("--output-dir", default="analysis_output", help="Output directory")
    parser.add_argument("--skip-esmfold", action="store_true", help="Skip ESMFold prediction (for CPU-only machines)")
    args = parser.parse_args()

    if not args.target and not args.all_targets:
        parser.error("Specify --target DNA_SEQUENCE or --all-targets")

    results = run_pipeline(
        csv_path=args.input,
        target_dna=args.target if not args.all_targets else None,
        output_dir=args.output_dir,
        skip_esmfold=args.skip_esmfold,
    )

    for target_seq, result in results.items():
        t = result["target"]
        print(f"\n{'='*60}")
        print(f"Target: {t.shorthand} ({t.sequence})")
        print(f"  Candidates: {t.candidate_count} → dedup: {t.unique_count} → filtered: {t.filtered_count}")
        print(f"  Clusters: {t.cluster_count}, Independent: {t.independent_count}")
        print(f"  Modules found: {len(result['modules'])}")
        if result["wiki_page"]:
            print(f"  Wiki page: {result['wiki_page']}")
        for m in result["modules"]:
            print(f"    Module {m.module_id}: residues {m.residue_range}, conservation={m.conservation_score:.2f}, in {m.occurrences} designs")
        for a in result["assessments"]:
            print(f"    Assessment: transferability={a.transferability_score:.2f}, confidence={a.confidence}")


if __name__ == "__main__":
    main()
