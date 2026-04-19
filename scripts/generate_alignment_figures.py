#!/usr/bin/env python3
"""Generate alignment figures showing convergent motifs across binders.

For each target with strong shared motifs, align the top candidates
around the shared motif and visualize the conservation.
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

TARGETS = {
    "HD": "GCTTAATTAGCG", "NFKB": "GGGGATTCCCCC", "HSTELO": "AGGGTTAGGGTT",
    "CAG": "CAGCAGCAGCAG", "OCT4pt1": "GGTGAAATGA",
}

SOURCE_COLORS = {
    "Baker Lab": "#2196F3", "Overnight": "#FF9800",
    "AutoRes": "#4CAF50", "Phase4": "#9C27B0",
}

AA_COLORS = {
    "R": "#E53935", "K": "#E53935", "H": "#E53935",  # positive
    "D": "#1E88E5", "E": "#1E88E5",  # negative
    "W": "#FF8F00", "F": "#FF8F00", "Y": "#FF8F00",  # aromatic
    "N": "#43A047", "Q": "#43A047", "S": "#43A047", "T": "#43A047",  # polar
    "A": "#BDBDBD", "G": "#BDBDBD", "V": "#BDBDBD", "L": "#BDBDBD",
    "I": "#BDBDBD", "P": "#BDBDBD", "M": "#BDBDBD", "C": "#BDBDBD",  # hydrophobic
}

MOTIFS = {
    "HD": [("WFAN", "Homeodomain recognition helix"), ("NPYP", "Interface anchor"), ("FTAAQ", "Scaffold contact")],
    "NFKB": [("GLTQ", "DNA-contacting loop"), ("ALGLT", "Extended loop")],
    "HSTELO": [("AILDA", "Scaffold helix")],
    "OCT4pt1": [("KALAA", "Helix packing")],
}


def load_candidates(n_per_source=10):
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


def find_motif_context(seq, motif, context=15):
    """Find motif in sequence, return context window."""
    idx = seq.find(motif)
    if idx == -1:
        for i in range(len(motif) - 1, 2, -1):
            for j in range(len(seq) - i + 1):
                if seq[j:j+i] in motif or motif[:i] == seq[j:j+i]:
                    idx = j
                    break
            if idx >= 0:
                break
    if idx == -1:
        return None, -1
    start = max(0, idx - context)
    end = min(len(seq), idx + len(motif) + context)
    return seq[start:end], idx - start


def draw_alignment(ax, sequences, motif_positions, labels, sources, motif, motif_len):
    """Draw color-coded alignment around motif."""
    n_seqs = len(sequences)
    max_len = max(len(s) for s in sequences) if sequences else 0
    ax.set_xlim(-0.5, max_len + 0.5)
    ax.set_ylim(-0.5, n_seqs + 0.5)
    ax.invert_yaxis()
    for i, (seq, mpos, label, src) in enumerate(zip(sequences, motif_positions, labels, sources)):
        for j, aa in enumerate(seq):
            is_motif = mpos >= 0 and mpos <= j < mpos + motif_len
            if is_motif:
                bg_color = "#FFEB3B"
                fontweight = "bold"
                fontsize = 7
            else:
                bg_color = AA_COLORS.get(aa, "#EEEEEE")
                fontweight = "normal"
                fontsize = 6
            alpha = 0.8 if is_motif else 0.3
            ax.add_patch(plt.Rectangle((j - 0.45, i - 0.4), 0.9, 0.8,
                                       facecolor=bg_color, alpha=alpha, edgecolor="none"))
            ax.text(j, i, aa, ha="center", va="center", fontsize=fontsize,
                    fontweight=fontweight, fontfamily="monospace",
                    color="black" if is_motif else "#555")
        src_color = SOURCE_COLORS.get(src, "#999")
        ax.text(-0.7, i, label, ha="right", va="center", fontsize=6, color=src_color, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def fig10_motif_alignments(candidates):
    """Create alignment figure for each target's convergent motifs."""
    targets_with_motifs = [t for t in ["HD", "NFKB", "HSTELO", "OCT4pt1"] if t in MOTIFS]
    n_panels = sum(len(MOTIFS[t]) for t in targets_with_motifs)
    fig, axes = plt.subplots(n_panels, 1, figsize=(16, n_panels * 2.2 + 1))
    if n_panels == 1:
        axes = [axes]
    panel_idx = 0
    for target in targets_with_motifs:
        cands = candidates.get(target, [])
        if not cands:
            continue
        for motif, desc in MOTIFS[target]:
            ax = axes[panel_idx]
            matching = []
            for c in cands:
                context, mpos = find_motif_context(c["sequence"], motif, context=12)
                if context and mpos >= 0:
                    matching.append((c, context, mpos))
            matching.sort(key=lambda x: -x[0]["iptm"])
            matching = matching[:8]
            if not matching:
                ax.text(0.5, 0.5, f"No matches for {motif}", transform=ax.transAxes, ha="center")
                panel_idx += 1
                continue
            seqs = [m[1] for m in matching]
            mpositions = [m[2] for m in matching]
            labels = [f"{m[0]['source'][:5]} {m[0]['iptm']:.3f}" for m in matching]
            sources = [m[0]["source"] for m in matching]
            draw_alignment(ax, seqs, mpositions, labels, sources, motif, len(motif))
            ax.set_title(f"{target} — {motif} ({desc}) | DNA: {TARGETS.get(target, '')}",
                         fontsize=10, fontweight="bold", loc="left")
            panel_idx += 1
    handles = [mpatches.Patch(color=c, label=s) for s, c in SOURCE_COLORS.items()]
    handles.append(mpatches.Patch(color="#FFEB3B", label="Shared motif"))
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9)
    fig.suptitle("Convergent DNA-Recognition Motifs Across Independent Designs",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(FIGURES_DIR / "fig10_motif_alignments.png", dpi=200)
    plt.close()
    print(f"Figure 10: fig10_motif_alignments.png ({n_panels} panels)")


def fig11_conservation_heatmap(candidates):
    """Per-position conservation for HD binders aligned on WFAN motif."""
    target = "HD"
    motif = "WFAN"
    cands = candidates.get(target, [])
    matching = []
    for c in cands:
        context, mpos = find_motif_context(c["sequence"], motif, context=15)
        if context and mpos >= 0:
            matching.append((c, context, mpos))
    matching.sort(key=lambda x: -x[0]["iptm"])
    matching = matching[:12]
    if not matching:
        return
    aligned = []
    for c, context, mpos in matching:
        padded = "-" * (15 - mpos) + context + "-" * 15
        center = 15
        window = padded[center - 15:center + len(motif) + 15]
        aligned.append(window)
    max_len = max(len(a) for a in aligned)
    aligned = [a.ljust(max_len, "-") for a in aligned]
    aas = "ACDEFGHIKLMNPQRSTVWY-"
    n_pos = len(aligned[0])
    n_seqs = len(aligned)
    freq_matrix = np.zeros((len(aas), n_pos))
    for j in range(n_pos):
        col = [a[j] for a in aligned]
        for k, aa in enumerate(aas):
            freq_matrix[k, j] = col.count(aa) / n_seqs
    conservation = np.zeros(n_pos)
    for j in range(n_pos):
        col = [a[j] for a in aligned if a[j] != "-"]
        if col:
            from collections import Counter
            counts = Counter(col)
            conservation[j] = counts.most_common(1)[0][1] / len(col)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), height_ratios=[3, 1], sharex=True)
    # Alignment
    for i, (c, ctx, mp) in enumerate(matching):
        for j, aa in enumerate(aligned[i]):
            if aa == "-":
                continue
            is_motif = 15 <= j < 15 + len(motif)
            color = "#FFEB3B" if is_motif else AA_COLORS.get(aa, "#EEE")
            alpha = 0.9 if is_motif else 0.4
            ax1.add_patch(plt.Rectangle((j - 0.45, i - 0.4), 0.9, 0.8,
                                         facecolor=color, alpha=alpha, edgecolor="none"))
            ax1.text(j, i, aa, ha="center", va="center", fontsize=6,
                     fontfamily="monospace", fontweight="bold" if is_motif else "normal")
        src_color = SOURCE_COLORS.get(c["source"], "#999")
        ax1.text(-1, i, f"{c['source'][:6]} {c['iptm']:.3f}", ha="right", va="center",
                 fontsize=7, color=src_color, fontweight="bold")
    ax1.set_xlim(-0.5, n_pos + 0.5)
    ax1.set_ylim(-0.5, n_seqs + 0.5)
    ax1.invert_yaxis()
    ax1.set_yticks([])
    ax1.set_xticks([])
    for spine in ax1.spines.values():
        spine.set_visible(False)
    ax1.set_title(f"HD Binders Aligned on WFAN Motif (DNA: GCTTAATTAGCG)", fontsize=12, fontweight="bold")
    # Conservation bar
    colors = ["#FFEB3B" if 15 <= j < 15 + len(motif) else ("#4CAF50" if conservation[j] > 0.6 else "#BDBDBD")
              for j in range(n_pos)]
    ax2.bar(range(n_pos), conservation, color=colors, width=0.9)
    ax2.set_ylabel("Conservation", fontsize=10)
    ax2.set_ylim(0, 1.1)
    ax2.axhline(y=0.5, color="gray", linestyle="--", linewidth=0.5)
    ax2.set_xlim(-0.5, n_pos + 0.5)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig11_hd_conservation.png", dpi=200)
    plt.close()
    print("Figure 11: fig11_hd_conservation.png")


if __name__ == "__main__":
    candidates = load_candidates(n_per_source=10)
    fig10_motif_alignments(candidates)
    fig11_conservation_heatmap(candidates)
    print(f"\nAlignment figures saved to {FIGURES_DIR}/")
