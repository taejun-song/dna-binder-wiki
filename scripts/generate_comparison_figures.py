#!/usr/bin/env python3
"""Generate comparison figures for top candidates across all methods."""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

TARGETS_ORDER = ["NFKB", "HD", "OCT4pt1", "PNRP1", "OCT4pt2", "CAG", "HSTELO", "TATA", "Dux4grna2"]
SOURCES = ["Baker Lab", "Overnight", "AutoRes", "Phase4"]
COLORS = {"Baker Lab": "#2196F3", "Overnight": "#FF9800", "AutoRes": "#4CAF50", "Phase4": "#9C27B0"}


def load_top10():
    rows = []
    f = Path("analysis_output/top10_per_target_method.csv")
    if not f.exists():
        return rows
    with open(f) as fh:
        for row in csv.DictReader(fh):
            row["ptm"] = float(row["ptm"])
            row["iptm"] = float(row["iptm"])
            row["length"] = int(row["length"]) if row["length"] else 0
            row["rank"] = int(row["rank"])
            rows.append(row)
    return rows


def fig6_top5_iptm_per_target(rows):
    """Grouped bar chart: top-5 ipTM per target, colored by source."""
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    for idx, target in enumerate(TARGETS_ORDER):
        ax = axes[idx // 3][idx % 3]
        t_rows = sorted([r for r in rows if r["target"] == target], key=lambda r: -r["iptm"])[:15]
        if not t_rows:
            ax.set_visible(False)
            continue
        names = []
        iptms = []
        colors = []
        for i, r in enumerate(t_rows[:10]):
            short = r["design_name"].split("/")[-1][:15] if "/" in r["design_name"] else r["design_name"][:15]
            names.append(f"#{i+1}")
            iptms.append(r["iptm"])
            colors.append(COLORS.get(r["source"], "#999"))
        y = np.arange(len(names))
        bars = ax.barh(y, iptms, color=colors, edgecolor="white", height=0.7)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8)
        ax.invert_yaxis()
        ax.axvline(x=0.7, color="red", linestyle="--", linewidth=1, alpha=0.5)
        ax.set_xlim(0.3, 0.85)
        ax.set_title(target, fontsize=12, fontweight="bold")
        ax.set_xlabel("ipTM", fontsize=9)
        for bar, r in zip(bars, t_rows[:10]):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                    f"{r['iptm']:.3f} {r['source'][:5]} L={r['length']}",
                    va="center", fontsize=6)
    handles = [plt.Rectangle((0,0),1,1, color=c) for c in COLORS.values()]
    fig.legend(handles, list(COLORS.keys()), loc="lower center", ncol=4, fontsize=10)
    fig.suptitle("Top 10 Candidates Per Target — All Methods", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(FIGURES_DIR / "fig6_top10_per_target.png", dpi=200)
    plt.close()
    print("Figure 6: fig6_top10_per_target.png")


def fig7_length_vs_iptm(rows):
    """Scatter: protein length vs ipTM for all top candidates, colored by source."""
    fig, ax = plt.subplots(figsize=(10, 7))
    for src in SOURCES:
        src_rows = [r for r in rows if r["source"] == src and r["length"] > 0]
        if not src_rows:
            continue
        lengths = [r["length"] for r in src_rows]
        iptms = [r["iptm"] for r in src_rows]
        ax.scatter(lengths, iptms, c=COLORS[src], label=f"{src} (n={len(src_rows)})",
                   alpha=0.6, s=40, edgecolors="white", linewidth=0.5)
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1, alpha=0.5, label="ipTM threshold")
    ax.set_xlabel("Protein Length (aa)", fontsize=13)
    ax.set_ylabel("ipTM", fontsize=13)
    ax.set_title("Protein Length vs ipTM — Top Candidates All Targets", fontsize=14, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(40, 300)
    ax.set_ylim(0.35, 0.85)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig7_length_vs_iptm.png", dpi=200)
    plt.close()
    print("Figure 7: fig7_length_vs_iptm.png")


def fig8_best_per_target_methods(rows):
    """Grouped bar: #1 from each method per target, side by side."""
    fig, ax = plt.subplots(figsize=(14, 6))
    targets = TARGETS_ORDER
    x = np.arange(len(targets))
    n_src = len(SOURCES)
    w = 0.8 / n_src
    for i, src in enumerate(SOURCES):
        vals = []
        for t in targets:
            cands = [r for r in rows if r["target"] == t and r["source"] == src and r["rank"] == 1]
            vals.append(cands[0]["iptm"] if cands else 0)
        offset = (i - n_src/2 + 0.5) * w
        bars = ax.bar(x + offset, vals, w, label=src, color=COLORS[src], edgecolor="white")
        for bar, val in zip(bars, vals):
            if val > 0.01:
                ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                        f"{val:.3f}", ha="center", va="bottom", fontsize=6, rotation=90)
    ax.axhline(y=0.7, color="red", linestyle="--", linewidth=1.5, alpha=0.7, label="Threshold")
    ax.set_ylabel("Best ipTM", fontsize=13)
    ax.set_title("Best ipTM Per Target — Method Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(targets, fontsize=10, rotation=30, ha="right")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 0.9)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig8_best_per_method.png", dpi=200)
    plt.close()
    print("Figure 8: fig8_best_per_method.png")


def fig9_length_distribution_by_source(rows):
    """Box plot: length distribution of top-10 per source."""
    fig, ax = plt.subplots(figsize=(8, 5))
    data = []
    labels = []
    for src in SOURCES:
        lengths = [r["length"] for r in rows if r["source"] == src and r["length"] > 0]
        if lengths:
            data.append(lengths)
            labels.append(f"{src}\n(n={len(lengths)})")
    bp = ax.boxplot(data, labels=labels, patch_artist=True, widths=0.6)
    for patch, src in zip(bp["boxes"], [s for s in SOURCES if any(r["source"]==s and r["length"]>0 for r in rows)]):
        patch.set_facecolor(COLORS[src])
        patch.set_alpha(0.6)
    ax.set_ylabel("Protein Length (aa)", fontsize=12)
    ax.set_title("Protein Length Distribution — Top Candidates by Source", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig9_length_distribution.png", dpi=200)
    plt.close()
    print("Figure 9: fig9_length_distribution.png")


if __name__ == "__main__":
    rows = load_top10()
    if not rows:
        print("ERROR: top10_per_target_method.csv not found")
        exit(1)
    print(f"Loaded {len(rows)} top-10 entries")
    fig6_top5_iptm_per_target(rows)
    fig7_length_vs_iptm(rows)
    fig8_best_per_target_methods(rows)
    fig9_length_distribution_by_source(rows)
    print(f"\nAll comparison figures saved to {FIGURES_DIR}/")
