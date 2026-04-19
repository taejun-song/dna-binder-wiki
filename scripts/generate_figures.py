#!/usr/bin/env python3
"""Generate figures for the DNA binder report.

Includes Baker Lab scores, overnight scores, and autoresearch scores.
"""
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

TARGETS_ORDER = ["NFKB", "HD", "OCT4pt1", "PNRP1", "OCT4pt2", "CAG", "HSTELO", "TATA", "Dux4grna2"]

BAKER_SEQS = {
    "HD_specblock_design82": "MGQGRLTAEEKAILDAWFEAHKDNPYPSDEELEELAKQTGRTVKQVRNWFRYQRKKVKYGYDPSLRGKRLSVEARRILTDWFLANLENPLPSDEEIKQLAKEAGITPYQVVVWFQNRRKEYNKKYKGLPLEELRKIFEEKFK",
    "HD_specblock_design94": "APVPPKPYGGVKRLPAEARRLLREWALENLDKLFEIVDSPEWKEWREEATEELVELTGLPRKQIENWLRYLRTKIKHMTKEEVRAWLESGKRVRTKLTAEQKAALEEAFARNPHPTDEELRELAERLGLTPWQIRNWFINRRQKVRKEEK",
    "NFKB_specblock_design66": "MVIKRGKWTPEEIAAINALYARNPHPDRAELEALAAELGTRTPQQIRDYIRRVIKGEELKKADPELKAEAEELKRRRRALGLTQADVGRLLGERFGEPRSASTISRIENMQVTKAGFERLLPRLVALLDALEAEAAA",
    "NFKB_specblock_design82": "RPWLTPELRARIEALRREYGTDYERIAARIPGVSAGQVQAFAREARIAAEQAAHPAEYAELRAEAAALKARRDALGLTQKDVAEAIGRSQGTISRFENCRMSIATLRRLGALIRAYLDEVEAARAA",
    "NFKB_specblock_design65": "MVIRRGKWTPEEIAAILALYAKNPHPNDAELEALAAELGTRTPQQIRDYIRRTIKGEELKKKYPELKKIAEELKRRRKELGLTQADVGELLGEEFGTPKSASTISRIENLKITKSGFLKALPRLIALLDRLEAEAAA",
    "PNRP1_specblock_design39": "TKRKPRVRLTAEQRARLDARFEEKLVLTDEEREELAKELGLSEIRIYNWFKYRRQKGKKEIAKARGRKKTTPEDTEELYKEHGQTKVKKPRLVKSDEQKAILDEAFKKNPYPNDEEIEELAKKTGLSKVQIYIWFQNRRYRAK",
}

OVERNIGHT_SEQS = {
    "OCT4pt1_18_model_0": "IRTRLNSRIIFTQEQIDVLKKAFELNTNPSEEEKKALAATVGTTAKQVQTWFTNRRTNLSNALIVSNFTQLFGNDALNQLRLQIHQEIEKAVVELCSDLKLSAADTRSAITAAVNNETVKRIKAH",
    "HD_19_model_3": "AAKPRTVWTALQKQTLEEWLNQHKDNPYPTKAERAKLAEDLNVTVTQVKNWFANRRQKLQAQDMGITYAEYLKKRSLCSADKNANTPIAQLEALIQKKEAQLAAAIALGAPESTILALENTTIDNLKKNLNK",
    "OCT4pt2_10_model_0": "DQIASLQKRLASSKPVVVKPLTPAQAYERLKAALLAATEPTLLKRAALLGTTVETLRALAAPDNTDLATAQSKYTQLATICAKKNAVQRKIRVKKELVSAQELAAIRNASVKALETADELAPNV",
    "HSTELO_2_model_0": "TTITVTKAELIALVEAFCADVNISFETLRTLIASKASKSAFSIADLVKAFEERHPAIKLIVNQANQHKAQNRVTFPQSAVDMLDALLVQKDYKPPTKAERTALAKRTSLTPAQIATWAANRRSNLAKKKAKNK",
}

AUTORES_SEQS = {
    "NFKB_autores": "ARVRVVRTPAQIAALLAAADQYASQGLSAAELNDLALRVGLTQAQVENWFANRQRKVNGRPSPTAAERANRKLAKNKNAAENAEALKASLNLLIDANM",
    "HD_autores": "AQFSAEQVAALEQAFAISQYPSTETKSALAAKTGLSETQIKVWFANRRSLAKAERAAQNVTKPSALEARARKAQKLGMTLAAVKAQVDSARQSSLAKAQEQRDNALASAQAALAAALHAAA",
    "OCT4pt1_autores": "GAEARASLLKDKIARYAVGTTSNAVTQLALALNSLGKAYVRNGDHSQAISALEAAIGLLDPLSPTFAASYVTALNNLGNAYSKAGKYVEAIKAYQQALKVAEKFSPTLKIDALTNLGVTLLKLGNAAAAKASLMQALALDPDHAAALATLQTIAA",
    "CAG_autores": "GAAAAAAAAAALLAAGNAALKAGSYAAAIAAYNQAIALNPTNAAAYLNLGNAYSKLGNTAAAIAAYNKALALNPNNTTAQINLAKAQGDAAAAAAIAAANAAANPAAALTQAGQTAAAIAALYQAAAATGSPAAQAAALNNLGAIYQAQGQLAAAIAAAYQAALALAAPTSPALAAALAANLAATQAALAA",
    "TATA_autores": "SHLAQAAAAKKKGDFDTAIALLNQVLLIAPAAKQANAYLALATALTAQGNLDKAQAALKKALAIQPSNTSAKLSLAAVLLKQGDVDKALALYRQLAAQGSTTARIKLANHFAQQGQLDAAVATLEAALADTAQNAPTSGARVALLLNLAGLYKKAARLDDAVQAYQQAAQVAQLINNAAAAASQAENNAANLEKAAT",
    "Dux4grna2_autores": "GAQQALNNKALTLLNQKQYADAIQVLDKMEELGFTPDLSTYLIRGDALINLGQVNAAIADYHSAIEKNPSLVDSATYKNLGNAYKKAGEYDNAIAQFNKAIELNPTNLTAYNNLANTYQDMGKNDLAIAAYDKAISLFPNSASAASATTNLGRVLASKGDVDAAVKAYENAISTAQKNKANVLAAISFQNLAAVFKAQGKSADAAAQLVASAAARLAANANSAQAYADLAEAFELLGKSADAATMQAKALTLA",
    "PNRP1_autores": "AAADSIAKGKQLIKAGQDAQAQALYEAVLKQFPDTAEAATAALNLGNLYMKQKKYDLAIQHYKKAAKLLPAAAYNNIGNAYLAQGLIDNAIAAYNKALELNPQYAAAYNNKGVAYKAKGKDDEAIADFNRALALNPNYNAARKNLGILQLKLNIPEGALLLNIANTYNSALNLLNKANAAALQAGDSQQARQLLEAALASLDSALAQTNDQDVALLSAKLSALENLAQIAEPSEFPSLAQRLVAVAQQLLAVGNLGAANRAQTAAQACTAAAT",
    "OCT4pt2_autores": "GSLDEELLQYQQLLQQVNSLARTKAALRVQIDQITAADSSDLETQQAVASLQAQQEALDLEIKALTEQIAATYPVLASEKNTANAEKRAAKTQAEVQSQTLQLEAQEKTLQLEALQILQI",
    "HSTELO_autores": "GSAVNQIIAAREKELILLAKHTSNVNDFVNKHMLAIISDLKALGITGFDPLVEKAKAELLSKCQINVIKQNQRNERVKKFKEDHSDVIAQAYAAAKQYVSDSAKLNQIVQTLTNLVTNQKILASQLVAAAQIAAHFYAATGKTPSSSEIMALISDAN",
}


def load_scores():
    baker = defaultdict(list)
    for f in Path("analysis_output/scores").glob("*_scores.tsv"):
        target = f.stem.replace("_scores", "")
        with open(f) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                baker[target].append({"name": row["name"], "ptm": float(row["ptm"]), "iptm": float(row["iptm"]), "source": "Baker Lab"})

    overnight = defaultdict(list)
    tsv = Path("analysis_output/overnight/results.tsv")
    if tsv.exists():
        with open(tsv) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                overnight[row["target"]].append({"name": row["name"], "ptm": float(row["ptm"]), "iptm": float(row["iptm"]), "source": "Overnight"})

    autores = defaultdict(list)
    for f in Path("analysis_output/autoresearch").glob("*_autoresearch.tsv"):
        target = f.stem.replace("_autoresearch", "")
        with open(f) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                n_scored = int(row.get("n_scored", 0))
                if n_scored > 0:
                    autores[target].append({"name": row["experiment"], "ptm": float(row["best_ptm"]), "iptm": float(row["best_iptm"]), "source": "AutoRes"})
    for f in Path("analysis_output/autoresearch").glob("*_results.tsv"):
        target = f.stem.replace("_results", "")
        if target in autores:
            continue
        with open(f) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                n_scored = int(row.get("n_scored", 0))
                if n_scored > 0:
                    autores[target].append({"name": row["experiment"], "ptm": float(row["best_ptm"]), "iptm": float(row["best_iptm"]), "source": "AutoRes"})

    return baker, overnight, autores


def fig1_iptm_comparison(baker, overnight, autores):
    fig, ax = plt.subplots(figsize=(12, 5))
    targets = TARGETS_ORDER
    x = np.arange(len(targets))
    w = 0.25
    baker_best = [max([d["iptm"] for d in baker.get(t, [{"iptm": 0}])]) for t in targets]
    overnight_best = [max([d["iptm"] for d in overnight.get(t, [{"iptm": 0}])]) for t in targets]
    autores_best = [max([d["iptm"] for d in autores.get(t, [{"iptm": 0}])]) for t in targets]
    ax.bar(x - w, baker_best, w, label="Baker Lab", color="#2196F3", edgecolor="white")
    ax.bar(x, overnight_best, w, label="Overnight", color="#FF9800", edgecolor="white")
    ax.bar(x + w, autores_best, w, label="Autoresearch", color="#4CAF50", edgecolor="white")
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1.5, alpha=0.7, label="Threshold (ipTM=0.7)")
    ax.set_ylabel("Best ipTM", fontsize=13)
    ax.set_title("Best ipTM Per Target: Baker Lab vs Overnight vs Autoresearch", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(targets, fontsize=10, rotation=30, ha="right")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 0.95)
    for bars, vals in [(ax.containers[0], baker_best), (ax.containers[1], overnight_best), (ax.containers[2], autores_best)]:
        for bar, val in zip(bars, vals):
            if val > 0.01:
                ax.text(bar.get_x() + bar.get_width()/2, val + 0.008, f"{val:.2f}", ha="center", va="bottom", fontsize=7, rotation=90)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_iptm_comparison.png", dpi=200)
    plt.close()
    print("Figure 1: fig1_iptm_comparison.png")


def fig2_score_distribution(baker, overnight, autores):
    fig, axes = plt.subplots(3, 3, figsize=(14, 10), sharey=True)
    for idx, target in enumerate(TARGETS_ORDER):
        ax = axes[idx // 3][idx % 3]
        b_iptm = [d["iptm"] for d in baker.get(target, [])]
        o_iptm = [d["iptm"] for d in overnight.get(target, [])]
        a_iptm = [d["iptm"] for d in autores.get(target, [])]
        bins = np.linspace(0.2, 0.85, 20)
        if b_iptm:
            ax.hist(b_iptm, bins=bins, alpha=0.5, color="#2196F3", label="Baker", density=True)
        if o_iptm:
            ax.hist(o_iptm, bins=bins, alpha=0.5, color="#FF9800", label="Overnight", density=True)
        if a_iptm:
            ax.hist(a_iptm, bins=bins, alpha=0.5, color="#4CAF50", label="AutoRes", density=True)
        ax.axvline(x=0.7, color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.set_title(target, fontsize=11, fontweight="bold")
        ax.set_xlim(0.2, 0.85)
        if idx == 0:
            ax.legend(fontsize=7)
    fig.supxlabel("ipTM", fontsize=12)
    fig.supylabel("Density", fontsize=12)
    fig.suptitle("ipTM Score Distributions by Source", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_score_distributions.png", dpi=200)
    plt.close()
    print("Figure 2: fig2_score_distributions.png")


def fig3_ptm_vs_iptm(baker, overnight, autores):
    fig, ax = plt.subplots(figsize=(9, 7))
    n_baker, n_overnight, n_autores = 0, 0, 0
    for target in TARGETS_ORDER:
        for d in baker.get(target, []):
            ax.scatter(d["ptm"], d["iptm"], color="#2196F3", alpha=0.5, s=30, edgecolors="none")
            n_baker += 1
        for d in overnight.get(target, []):
            ax.scatter(d["ptm"], d["iptm"], color="#FF9800", alpha=0.3, s=20, edgecolors="none")
            n_overnight += 1
        for d in autores.get(target, []):
            ax.scatter(d["ptm"], d["iptm"], color="#4CAF50", alpha=0.3, s=15, edgecolors="none")
            n_autores += 1
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1, alpha=0.5)
    ax.axvline(x=0.8, color="red", linestyle="--", linewidth=1, alpha=0.5)
    ax.fill_between([0.8, 1.0], 0.7, 1.0, alpha=0.08, color="green")
    ax.text(0.88, 0.73, "PASS", fontsize=12, color="green", fontweight="bold", ha="center")
    ax.set_xlabel("pTM (fold confidence)", fontsize=12)
    ax.set_ylabel("ipTM (interface confidence)", fontsize=12)
    ax.set_title("pTM vs ipTM: All Scored Designs", fontsize=14, fontweight="bold")
    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.2, 0.9)
    ax.legend(handles=[
        mpatches.Patch(color="#2196F3", alpha=0.6, label=f"Baker Lab (n={n_baker})"),
        mpatches.Patch(color="#FF9800", alpha=0.6, label=f"Overnight (n={n_overnight})"),
        mpatches.Patch(color="#4CAF50", alpha=0.6, label=f"AutoRes (n={n_autores})"),
    ], fontsize=9)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_ptm_vs_iptm.png", dpi=200)
    plt.close()
    print(f"Figure 3: fig3_ptm_vs_iptm.png (Baker={n_baker}, Overnight={n_overnight}, AutoRes={n_autores})")


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
    for k, v in BAKER_SEQS.items():
        all_seqs[f"B:{k.split('_')[0]}"] = v
    for k, v in OVERNIGHT_SEQS.items():
        all_seqs[f"O:{k.split('_')[0]}"] = v
    for k, v in AUTORES_SEQS.items():
        all_seqs[f"A:{k.split('_')[0]}"] = v
    # Deduplicate keys by appending index
    unique_seqs = {}
    counts = defaultdict(int)
    for k, v in all_seqs.items():
        counts[k] += 1
        if counts[k] > 1:
            unique_seqs[f"{k}_{counts[k]}"] = v
        else:
            unique_seqs[k] = v
    names = list(unique_seqs.keys())
    seqs = list(unique_seqs.values())
    n = len(names)
    matrix = np.zeros((n, n))
    for i in range(n):
        matrix[i, i] = 1.0
        for j in range(i + 1, n):
            identity = pairwise_identity(seqs[i], seqs[j])
            matrix[i, j] = identity
            matrix[j, i] = identity
    fig, ax = plt.subplots(figsize=(14, 11))
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=0.6)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(names, fontsize=7)
    for i in range(n):
        for j in range(n):
            val = matrix[i, j]
            color = "white" if val > 0.35 else "black"
            ax.text(j, i, f"{val:.0%}", ha="center", va="center", fontsize=5, color=color)
    cbar = plt.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label("Sequence Identity", fontsize=11)
    ax.set_title("Sequence Identity: Baker Lab (B:) vs Overnight (O:) vs AutoRes (A:)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_sequence_similarity.png", dpi=200)
    plt.close()
    print("Figure 4: fig4_sequence_similarity.png")


def fig5_aa_composition():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    aas = "ACDEFGHIKLMNPQRSTVWY"
    baker_all = "".join(BAKER_SEQS.values())
    overnight_all = "".join(OVERNIGHT_SEQS.values())
    autores_all = "".join(AUTORES_SEQS.values())
    baker_freq = {aa: baker_all.count(aa) / len(baker_all) for aa in aas}
    overnight_freq = {aa: overnight_all.count(aa) / len(overnight_all) for aa in aas}
    autores_freq = {aa: autores_all.count(aa) / len(autores_all) for aa in aas}
    x = np.arange(len(aas))
    w = 0.25
    ax = axes[0]
    ax.bar(x - w, [baker_freq[aa] for aa in aas], w, label="Baker Lab", color="#2196F3")
    ax.bar(x, [overnight_freq[aa] for aa in aas], w, label="Overnight", color="#FF9800")
    ax.bar(x + w, [autores_freq[aa] for aa in aas], w, label="AutoRes", color="#4CAF50")
    ax.set_xticks(x)
    ax.set_xticklabels(list(aas), fontsize=9)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title("Amino Acid Composition", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)

    ax2 = axes[1]
    key_res = ["A", "R", "K", "E", "L", "W", "N", "Q"]
    labels = ["Ala", "Arg", "Lys", "Glu", "Leu", "Trp", "Asn", "Gln"]
    x2 = np.arange(len(key_res))
    ax2.bar(x2 - w, [baker_freq[aa] for aa in key_res], w, label="Baker Lab", color="#2196F3")
    ax2.bar(x2, [overnight_freq[aa] for aa in key_res], w, label="Overnight", color="#FF9800")
    ax2.bar(x2 + w, [autores_freq[aa] for aa in key_res], w, label="AutoRes", color="#4CAF50")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("Frequency", fontsize=11)
    ax2.set_title("Key Residues for DNA Binding", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_aa_composition.png", dpi=200)
    plt.close()
    print("Figure 5: fig5_aa_composition.png")


if __name__ == "__main__":
    baker, overnight, autores = load_scores()
    fig1_iptm_comparison(baker, overnight, autores)
    fig2_score_distribution(baker, overnight, autores)
    fig3_ptm_vs_iptm(baker, overnight, autores)
    fig4_sequence_similarity()
    fig5_aa_composition()
    print(f"\nAll figures saved to {FIGURES_DIR}/")
