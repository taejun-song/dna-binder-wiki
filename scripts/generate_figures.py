#!/usr/bin/env python3
"""Generate figures for the DNA binder report."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
from Bio import Align

sns.set_theme(style="whitegrid", font_scale=1.1)

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

TARGETS_ORDER = ["HD", "NFKB", "PNRP1", "OCT4pt1", "OCT4pt2", "HSTELO", "CAG"]

BAKER_SEQS = {
    "HD_specblock_design82": "MGQGRLTAEEKAILDAWFEAHKDNPYPSDEELEELAKQTGRTVKQVRNWFRYQRKKVKYGYDPSLRGKRLSVEARRILTDWFLANLENPLPSDEEIKQLAKEAGITPYQVVVWFQNRRKEYNKKYKGLPLEELRKIFEEKFK",
    "HD_specblock_design94": "APVPPKPYGGVKRLPAEARRLLREWALENLDKLFEIVDSPEWKEWREEATEELVELTGLPRKQIENWLRYLRTKIKHMTKEEVRAWLESGKRVRTKLTAEQKAALEEAFARNPHPTDEELRELAERLGLTPWQIRNWFINRRQKVRKEEK",
    "NFKB_specblock_design66": "MVIKRGKWTPEEIAAINALYARNPHPDRAELEALAAELGTRTPQQIRDYIRRVIKGEELKKADPELKAEAEELKRRRRALGLTQADVGRLLGERFGEPRSASTISRIENMQVTKAGFERLLPRLVALLDALEAEAAA",
    "NFKB_specblock_design82": "RPWLTPELRARIEALRREYGTDYERIAARIPGVSAGQVQAFAREARIAAEQAAHPAEYAELRAEAAALKARRDALGLTQKDVAEAIGRSQGTISRFENCRMSIATLRRLGALIRAYLDEVEAARAA",
    "NFKB_specblock_design65": "MVIRRGKWTPEEIAAILALYAKNPHPNDAELEALAAELGTRTPQQIRDYIRRTIKGEELKKKYPELKKIAEELKRRRKELGLTQADVGELLGEEFGTPKSASTISRIENLKITKSGFLKALPRLIALLDRLEAEAAA",
    "PNRP1_specblock_design39": "TKRKPRVRLTAEQRARLDARFEEKLVLTDEEREELAKELGLSEIRIYNWFKYRRQKGKKEIAKARGRKKTTPEDTEELYKEHGQTKVKKPRLVKSDEQKAILDEAFKKNPYPNDEEIEELAKKTGLSKVQIYIWFQNRRYRAK",
}
OURS_SEQS = {
    "OCT4pt1_18_model_0": "IRTRLNSRIIFTQEQIDVLKKAFELNTNPSEEEKKALAATVGTTAKQVQTWFTNRRTNLSNALIVSNFTQLFGNDALNQLRLQIHQEIEKAVVELCSDLKLSAADTRSAITAAVNNETVKRIKAH",
    "NFKB_24_model_6": "TRKITLTDRDAQILDILQERYSGLTPSATARKQIAIELNISEATVSSHFKKLRKAGLVTAKAAGARALTLTDAQREKIADIAKVAYDMCQQQGVSGINQKIVANFIQELIKQGVSLDELTAEYIVSEILKKYA",
    "OCT4pt2_10_model_0": "DQIASLQKRLASSKPVVVKPLTPAQAYERLKAALLAATEPTLLKRAALLGTTVETLRALAAPDNTDLATAQSKYTQLATICAKKNAVQRKIRVKKELVSAQELAAIRNASVKALETADELAPNV",
    "HSTELO_2_model_0": "TTITVTKAELIALVEAFCADVNISFETLRTLIASKASKSAFSIADLVKAFEERHPAIKLIVNQANQHKAQNRVTFPQSAVDMLDALLVQKDYKPPTKAERTALAKRTSLTPAQIATWAANRRSNLAKKKAKNK",
    "PNRP1_9_model_2": "MNQTKVEEILAAKGLTALQVIQAVSAAARAGQSRTAFLKSTFGLSEAEAAAVVAYINATNKNANEKKAAQLGLTYKQFMSIKRSRSKQFKALTGISLSAYAAALRAAGKSAEQVAAKIADLKQQFGLKSNAELLKEAA",
    "CAG_0_model_4": "MSLVQKKILVDYAKAHLNTDPTEAEISALAVQLNVSPLTISNSIVAFRKKIAAGYSEDAILQNKKAITAAEAELCAQLIAEILNQNLSFAEALAEATRRCSDIGLSELVKATLRESITNAFKRA",
}


def load_scores():
    baker = defaultdict(list)
    for f in Path("analysis_output/scores").glob("*_scores.tsv"):
        target = f.stem.replace("_scores", "")
        with open(f) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                baker[target].append({
                    "name": row["name"],
                    "ptm": float(row["ptm"]),
                    "iptm": float(row["iptm"]),
                    "source": "Baker Lab",
                })

    ours = defaultdict(list)
    tsv = Path("analysis_output/overnight/results.tsv")
    if tsv.exists():
        with open(tsv) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                ours[row["target"]].append({
                    "name": row["name"],
                    "ptm": float(row["ptm"]),
                    "iptm": float(row["iptm"]),
                    "source": "Ours",
                })
    return baker, ours


def fig1_iptm_comparison(baker, ours):
    fig, ax = plt.subplots(figsize=(10, 5))
    targets = [t for t in TARGETS_ORDER if t in baker or t in ours]
    x = np.arange(len(targets))
    w = 0.35
    baker_best = [max([d["iptm"] for d in baker.get(t, [{"iptm": 0}])]) for t in targets]
    ours_best = [max([d["iptm"] for d in ours.get(t, [{"iptm": 0}])]) for t in targets]
    bars1 = ax.bar(x - w/2, baker_best, w, label="Baker Lab (best)", color="#2196F3", edgecolor="white")
    bars2 = ax.bar(x + w/2, ours_best, w, label="Ours (best)", color="#FF5722", edgecolor="white")
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1.5, alpha=0.7, label="Threshold (ipTM=0.7)")
    ax.set_ylabel("Best ipTM", fontsize=13)
    ax.set_title("Best ipTM Per Target: Baker Lab vs Our Designs", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(targets, fontsize=11)
    ax.legend(fontsize=10, loc="upper right")
    ax.set_ylim(0, 0.95)
    for bar, val in zip(bars1, baker_best):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.01, f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    for bar, val in zip(bars2, ours_best):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.01, f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_iptm_comparison.png", dpi=200)
    plt.close()
    print("Figure 1: fig1_iptm_comparison.png")


def fig2_score_distribution(baker, ours):
    fig, axes = plt.subplots(2, 4, figsize=(14, 6), sharey=True)
    targets = [t for t in TARGETS_ORDER if t in baker]
    for idx, target in enumerate(targets):
        ax = axes[idx // 4][idx % 4]
        b_iptm = [d["iptm"] for d in baker.get(target, [])]
        o_iptm = [d["iptm"] for d in ours.get(target, [])]
        if b_iptm:
            ax.hist(b_iptm, bins=15, alpha=0.6, color="#2196F3", label="Baker", density=True)
        if o_iptm:
            ax.hist(o_iptm, bins=15, alpha=0.6, color="#FF5722", label="Ours", density=True)
        ax.axvline(x=0.7, color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.set_title(target, fontsize=11, fontweight="bold")
        ax.set_xlim(0.3, 0.9)
        if idx == 0:
            ax.legend(fontsize=8)
    if len(targets) < 8:
        axes[1][3].set_visible(False)
    fig.supxlabel("ipTM", fontsize=12)
    fig.supylabel("Density", fontsize=12)
    fig.suptitle("ipTM Score Distributions: Baker Lab vs Ours", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_score_distributions.png", dpi=200)
    plt.close()
    print("Figure 2: fig2_score_distributions.png")


def fig3_ptm_vs_iptm(baker, ours):
    fig, ax = plt.subplots(figsize=(8, 6))
    for target in TARGETS_ORDER:
        for d in baker.get(target, []):
            ax.scatter(d["ptm"], d["iptm"], color="#2196F3", alpha=0.4, s=30, edgecolors="none")
        for d in ours.get(target, []):
            ax.scatter(d["ptm"], d["iptm"], color="#FF5722", alpha=0.3, s=20, edgecolors="none")
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1, alpha=0.5)
    ax.axvline(x=0.8, color="red", linestyle="--", linewidth=1, alpha=0.5)
    ax.fill_between([0.8, 1.0], 0.7, 1.0, alpha=0.08, color="green")
    ax.text(0.88, 0.73, "PASS", fontsize=12, color="green", fontweight="bold", ha="center")
    ax.set_xlabel("pTM (fold confidence)", fontsize=12)
    ax.set_ylabel("ipTM (interface confidence)", fontsize=12)
    ax.set_title("pTM vs ipTM: All Scored Designs", fontsize=14, fontweight="bold")
    ax.set_xlim(0.5, 1.0)
    ax.set_ylim(0.3, 0.9)
    baker_patch = mpatches.Patch(color="#2196F3", alpha=0.6, label=f"Baker Lab (n={sum(len(v) for v in baker.values())})")
    ours_patch = mpatches.Patch(color="#FF5722", alpha=0.6, label=f"Ours (n={sum(len(v) for v in ours.values())})")
    ax.legend(handles=[baker_patch, ours_patch], fontsize=10)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_ptm_vs_iptm.png", dpi=200)
    plt.close()
    print("Figure 3: fig3_ptm_vs_iptm.png")


def pairwise_identity(seq1, seq2):
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 1
    aligner.mismatch_score = 0
    aligner.open_gap_score = -2
    aligner.extend_gap_score = -0.5
    alignments = aligner.align(seq1, seq2)
    if not alignments:
        return 0.0
    best = alignments[0]
    matches = sum(1 for a, b in zip(best[0], best[1]) if a == b and a != "-")
    return matches / max(len(seq1), len(seq2))


def fig4_sequence_similarity():
    all_seqs = {}
    all_seqs.update(BAKER_SEQS)
    all_seqs.update(OURS_SEQS)
    names = list(all_seqs.keys())
    n = len(names)
    matrix = np.zeros((n, n))
    for i in range(n):
        matrix[i, i] = 1.0
        for j in range(i + 1, n):
            identity = pairwise_identity(all_seqs[names[i]], all_seqs[names[j]])
            matrix[i, j] = identity
            matrix[j, i] = identity

    short_names = []
    for name in names:
        if name in BAKER_SEQS:
            parts = name.split("_")
            short_names.append(f"B:{parts[0]}_{parts[-1]}")
        else:
            parts = name.split("_")
            short_names.append(f"O:{parts[0]}_{parts[-1]}")

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=0.6)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(short_names, fontsize=9)
    for i in range(n):
        for j in range(n):
            val = matrix[i, j]
            color = "white" if val > 0.35 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Sequence Identity", fontsize=11)
    ax.set_title("Sequence Identity: Baker Lab (B:) vs Ours (O:)\nTop Candidates Across All Targets", fontsize=13, fontweight="bold")
    # Add separator line between Baker and Ours
    n_baker = len(BAKER_SEQS)
    ax.axhline(y=n_baker - 0.5, color="white", linewidth=2)
    ax.axvline(x=n_baker - 0.5, color="white", linewidth=2)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_sequence_similarity.png", dpi=200)
    plt.close()
    print("Figure 4: fig4_sequence_similarity.png")
    print("\nPairwise identities between Baker and Ours:")
    for i, bn in enumerate(names[:n_baker]):
        for j, on in enumerate(names[n_baker:]):
            print(f"  {bn} vs {on}: {matrix[i, n_baker+j]:.3f}")


def fig5_aa_composition():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    aas = "ACDEFGHIKLMNPQRSTVWY"

    baker_all = "".join(BAKER_SEQS.values())
    ours_all = "".join(OURS_SEQS.values())

    baker_freq = {aa: baker_all.count(aa) / len(baker_all) for aa in aas}
    ours_freq = {aa: ours_all.count(aa) / len(ours_all) for aa in aas}

    x = np.arange(len(aas))
    w = 0.35
    ax = axes[0]
    ax.bar(x - w/2, [baker_freq[aa] for aa in aas], w, label="Baker Lab", color="#2196F3")
    ax.bar(x + w/2, [ours_freq[aa] for aa in aas], w, label="Ours", color="#FF5722")
    ax.set_xticks(x)
    ax.set_xticklabels(list(aas), fontsize=10)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title("Amino Acid Composition", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    # Charged residues (R, K, D, E) comparison
    ax2 = axes[1]
    charged = ["R", "K", "D", "E"]
    baker_charged = [baker_freq[aa] for aa in charged]
    ours_charged = [ours_freq[aa] for aa in charged]
    x2 = np.arange(len(charged))
    ax2.bar(x2 - w/2, baker_charged, w, label="Baker Lab", color="#2196F3")
    ax2.bar(x2 + w/2, ours_charged, w, label="Ours", color="#FF5722")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(["Arg (R)", "Lys (K)", "Asp (D)", "Glu (E)"], fontsize=10)
    ax2.set_ylabel("Frequency", fontsize=11)
    ax2.set_title("Charged Residues\n(DNA-contact key residues)", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_aa_composition.png", dpi=200)
    plt.close()
    print("Figure 5: fig5_aa_composition.png")


if __name__ == "__main__":
    baker, ours = load_scores()
    fig1_iptm_comparison(baker, ours)
    fig2_score_distribution(baker, ours)
    fig3_ptm_vs_iptm(baker, ours)
    fig4_sequence_similarity()
    fig5_aa_composition()
    print(f"\nAll figures saved to {FIGURES_DIR}/")
