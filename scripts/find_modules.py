#!/usr/bin/env python3
"""Find modular DNA-recognition elements across binders for the same target.

For each target:
1. Collect top N binders (all sources)
2. Find shared k-mer motifs across independently generated designs
3. Score motifs by frequency and cross-source occurrence
4. Identify candidate modular recognition elements

A motif is "modular" if it appears in binders from different generation
runs (different sources or different experiments), suggesting convergent
evolution toward a shared DNA-recognition strategy.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}


def load_top_candidates(n_per_source=10):
    """Load top candidates per target from the full CSV."""
    candidates = defaultdict(list)
    f = Path("analysis_output/all_candidates_full.csv")
    with open(f) as fh:
        reader = csv.DictReader(fh)
        counts = defaultdict(lambda: defaultdict(int))
        for row in reader:
            t = row["target"]
            src = row["source"]
            seq = row["sequence"]
            if not seq or len(seq) < 50:
                continue
            if counts[t][src] >= n_per_source:
                continue
            counts[t][src] += 1
            candidates[t].append({
                "name": row["design_name"],
                "source": src,
                "sequence": seq,
                "iptm": float(row["iptm"]),
                "length": len(seq),
            })
    return candidates


def extract_kmers(seq, k):
    return [seq[i:i+k] for i in range(len(seq) - k + 1)]


def find_shared_motifs(sequences, sources, k_range=(5, 12)):
    """Find k-mers shared across sequences from different sources."""
    motifs = []
    for k in range(k_range[0], k_range[1] + 1):
        kmer_to_seqs = defaultdict(set)
        kmer_to_sources = defaultdict(set)
        for i, (seq, src) in enumerate(zip(sequences, sources)):
            for kmer in set(extract_kmers(seq, k)):
                kmer_to_seqs[kmer].add(i)
                kmer_to_sources[kmer].add(src)
        for kmer, seq_ids in kmer_to_seqs.items():
            n_sources = len(kmer_to_sources[kmer])
            n_seqs = len(seq_ids)
            if n_seqs >= 3 and n_sources >= 2:
                motifs.append({
                    "motif": kmer,
                    "k": k,
                    "n_sequences": n_seqs,
                    "n_sources": n_sources,
                    "sources": sorted(kmer_to_sources[kmer]),
                    "seq_indices": sorted(seq_ids),
                    "score": n_seqs * n_sources * k,
                })
    motifs.sort(key=lambda m: -m["score"])
    return motifs


def remove_redundant_motifs(motifs, max_results=20):
    """Remove motifs that are substrings of higher-scoring ones."""
    kept = []
    for m in motifs:
        is_sub = False
        for k in kept:
            if m["motif"] in k["motif"]:
                is_sub = True
                break
        if not is_sub:
            kept.append(m)
        if len(kept) >= max_results:
            break
    return kept


def find_cross_target_motifs(all_motifs, min_targets=2, k_min=5):
    """Find motifs that appear across multiple targets."""
    motif_targets = defaultdict(set)
    motif_info = {}
    for target, motifs in all_motifs.items():
        for m in motifs:
            key = m["motif"]
            motif_targets[key].add(target)
            if key not in motif_info:
                motif_info[key] = m
    cross = []
    for motif, targets in motif_targets.items():
        if len(targets) >= min_targets and len(motif) >= k_min:
            cross.append({
                "motif": motif,
                "targets": sorted(targets),
                "n_targets": len(targets),
                "k": len(motif),
            })
    cross.sort(key=lambda m: (-m["n_targets"], -m["k"]))
    return cross[:30]


def main():
    candidates = load_top_candidates(n_per_source=10)
    all_motifs = {}
    print("=" * 70)
    print("MODULAR DNA-RECOGNITION ELEMENT ANALYSIS")
    print("=" * 70)

    for target in sorted(TARGETS):
        cands = candidates.get(target, [])
        if len(cands) < 3:
            continue
        sequences = [c["sequence"] for c in cands]
        sources = [c["source"] for c in cands]
        n_by_src = Counter(sources)
        print(f"\n{'='*60}")
        print(f"TARGET: {target} (DNA: {TARGETS[target]})")
        print(f"Candidates: {len(cands)} ({', '.join(f'{s}:{n}' for s,n in n_by_src.most_common())})")
        print(f"{'='*60}")
        motifs = find_shared_motifs(sequences, sources, k_range=(5, 15))
        motifs = remove_redundant_motifs(motifs, max_results=15)
        all_motifs[target] = motifs
        if not motifs:
            print("  No shared motifs found across sources.")
            continue
        print(f"\n  Top shared motifs (present in >=3 seqs, >=2 sources):")
        print(f"  {'Motif':<20s} {'Len':>3s} {'#Seq':>4s} {'#Src':>4s} {'Sources':<30s}")
        print(f"  {'-'*20} {'-'*3} {'-'*4} {'-'*4} {'-'*30}")
        for m in motifs[:10]:
            src_str = ",".join(m["sources"])
            print(f"  {m['motif']:<20s} {m['k']:>3d} {m['n_sequences']:>4d} {m['n_sources']:>4d} {src_str:<30s}")
        # Show which candidates contain the top motif
        if motifs:
            top = motifs[0]
            print(f"\n  Top motif '{top['motif']}' found in:")
            for idx in top["seq_indices"][:5]:
                c = cands[idx]
                pos = c["sequence"].find(top["motif"])
                context_start = max(0, pos - 5)
                context_end = min(len(c["sequence"]), pos + len(top["motif"]) + 5)
                context = c["sequence"][context_start:context_end]
                print(f"    {c['source']:12s} ipTM={c['iptm']:.3f} L={c['length']:3d} ...{context}...")

    # Cross-target analysis
    print(f"\n{'='*60}")
    print("CROSS-TARGET SHARED MOTIFS")
    print(f"{'='*60}")
    cross = find_cross_target_motifs(all_motifs, min_targets=2, k_min=5)
    if cross:
        print(f"\n  {'Motif':<20s} {'Len':>3s} {'#Targets':>8s} {'Targets':<40s}")
        print(f"  {'-'*20} {'-'*3} {'-'*8} {'-'*40}")
        for m in cross[:15]:
            print(f"  {m['motif']:<20s} {m['k']:>3d} {m['n_targets']:>8d} {','.join(m['targets']):<40s}")
    else:
        print("  No motifs shared across multiple targets.")
    print(f"\n  Note: Cross-target motifs suggest general DNA-binding modules.")
    print(f"  Target-specific motifs suggest sequence-specific recognition.")

    # Write results
    out = Path("analysis_output/module_analysis.txt")
    # Re-run with output capture would be redundant; the print output is the report


if __name__ == "__main__":
    main()
