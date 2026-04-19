#!/usr/bin/env python3
"""Phase 4 autoresearch: deeper exploration for gap targets.

Focuses on HD, PNRP1, OCT4pt2, HSTELO with unexplored parameter
combinations and larger batch sizes. Uses 1BNA (which works) as template.

New strategies:
- Combined parameter sweeps (length + sampler jointly)
- Finer-grained length ranges around previous optima
- s_trans variations
- Higher timestep counts
- is_non_loopy toggle with best sampler
"""
import copy
import gzip
import json
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime
from itertools import product
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}

PREV_BEST = {
    "HD": {"iptm": 0.733, "config": {"length": "110-130"}, "sampler": {}},
    "PNRP1": {"iptm": 0.662, "config": {"length": "250-300"}, "sampler": {"use_classifier_free_guidance": True, "cfg_scale": 1.5, "num_timesteps": 200}},
    "OCT4pt2": {"iptm": 0.634, "config": {"length": "120-140"}, "sampler": {"gamma_0": 0.3}},
    "HSTELO": {"iptm": 0.600, "config": {"length": "140-180"}, "sampler": {}},
}

AA3TO1 = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G", "HIS": "H",
    "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q",
    "ARG": "R", "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
}
BIN_DIR = Path(sys.executable).parent
CKPT = Path.home() / ".foundry/checkpoints/rfd3_latest.ckpt"
DNA_PDB = Path("data/dna_templates/1BNA.pdb").resolve()


def log_msg(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


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


def get_contig(target_name, length_range):
    seq = TARGETS[target_name]
    n = min(len(seq), 12)
    b_start, b_end = 13, 13 + n - 1
    return f"A1-{n},/0,B{b_start}-{b_end},/0,{length_range}"


def run_experiment(target_name, config_overrides, sampler_overrides, exp_dir, n_designs=20):
    exp_dir = Path(exp_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)
    rfd3_out = exp_dir / "rfd3_output"
    length_range = config_overrides.pop("length", "120-140")
    contig = get_contig(target_name, length_range)
    config = {"design": {"input": str(DNA_PDB), "contig": contig, "is_non_loopy": config_overrides.get("is_non_loopy", True)}}
    for k, v in config_overrides.items():
        if k not in ("length", "is_non_loopy"):
            config["design"][k] = v
    config_path = exp_dir / "config.json"
    config_path.write_text(json.dumps(config))
    cmd = [str(BIN_DIR / "rfd3"), f"out_dir={rfd3_out}", f"inputs={config_path}", f"n_batches={n_designs}", f"ckpt_path={CKPT}"]
    for k, v in sampler_overrides.items():
        if isinstance(v, bool):
            v = str(v).lower()
        cmd.append(f"inference_sampler.{k}={v}")
    subprocess.run(cmd, stdout=open(exp_dir / "rfd3.log", "w"), stderr=subprocess.STDOUT, timeout=900)
    cifs = sorted(rfd3_out.rglob("*.cif.gz")) if rfd3_out.exists() else []
    if not cifs:
        return 0.0, 0.0, 0.0, 0
    dna_seq = TARGETS[target_name]
    rf3_inputs = []
    for cif in cifs:
        seq = extract_seq(cif)
        if seq and len(seq) >= 50:
            rf3_inputs.append({"name": cif.stem.replace(".cif", ""), "components": [{"seq": seq, "chain_id": "A"}, {"seq": dna_seq, "chain_id": "B"}]})
    if not rf3_inputs:
        return 0.0, 0.0, 0.0, 0
    rf3_dir = exp_dir / "rf3"
    rf3_dir.mkdir(exist_ok=True)
    input_path = rf3_dir / "inputs.json"
    input_path.write_text(json.dumps(rf3_inputs))
    subprocess.run([str(BIN_DIR / "rf3"), "fold", f"inputs={input_path}", f"out_dir={rf3_dir}/results"], stdout=open(rf3_dir / "rf3.log", "w"), stderr=subprocess.STDOUT, timeout=1800)
    scores = []
    for inp in rf3_inputs:
        summaries = list((rf3_dir / "results").rglob(f"*{inp['name']}*summary_confidences*"))
        if summaries:
            with open(summaries[0]) as f:
                data = json.load(f)
            scores.append((data.get("iptm", 0.0), data.get("ptm", 0.0)))
    if not scores:
        return 0.0, 0.0, 0.0, 0
    best_iptm = max(s[0] for s in scores)
    mean_iptm = sum(s[0] for s in scores) / len(scores)
    best_ptm = max(s[1] for s in scores if s[0] == best_iptm)
    return best_iptm, mean_iptm, best_ptm, len(scores)


def run_phase4(target_name, base_dir, n_designs=20):
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    results_file = base_dir / f"{target_name}_phase4.tsv"
    prev = PREV_BEST[target_name]
    best_ever = prev["iptm"]
    best_config = copy.deepcopy(prev["config"])
    best_sampler = copy.deepcopy(prev["sampler"])
    exp_count = 0

    def log_result(exp_id, change, best_iptm, mean_iptm, best_ptm, n_scored, status):
        write_header = not results_file.exists() or results_file.stat().st_size == 0
        with open(results_file, "a") as f:
            if write_header:
                f.write("timestamp\texperiment\ttarget\tchange\tn_scored\tbest_iptm\tmean_iptm\tbest_ptm\tstatus\n")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts}\t{exp_id}\t{target_name}\t{change}\t{n_scored}\t{best_iptm:.4f}\t{mean_iptm:.4f}\t{best_ptm:.4f}\t{status}\n")

    def try_exp(change, config_override=None, sampler_override=None):
        nonlocal exp_count, best_ever, best_config, best_sampler
        exp_count += 1
        exp_id = f"p4_{exp_count:03d}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        cfg = copy.deepcopy(best_config)
        samp = copy.deepcopy(best_sampler)
        if config_override:
            cfg.update(config_override)
        if sampler_override:
            samp.update(sampler_override)
        iptm, mean, ptm, n = run_experiment(target_name, cfg, samp, base_dir / target_name / exp_id, n_designs)
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            if config_override:
                best_config.update(config_override)
            if sampler_override:
                best_sampler.update(sampler_override)
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")
        return iptm

    log_msg(f"[{target_name}] Phase 4 start. Previous best: {best_ever:.4f}")

    # Fine-grained length around previous optimum
    prev_len = best_config.get("length", "120-140")
    parts = prev_len.split("-")
    center = (int(parts[0]) + int(parts[1])) // 2
    for delta in [-20, -10, +10, +20]:
        lo = max(50, center + delta - 15)
        hi = center + delta + 15
        try_exp(f"length={lo}-{hi}", config_override={"length": f"{lo}-{hi}"})

    # s_trans variations
    for s_trans in [0.5, 0.75, 1.5, 2.0]:
        try_exp(f"s_trans={s_trans}", sampler_override={"s_trans": s_trans})

    # Timestep variations
    for ts in [100, 200, 300, 500]:
        try_exp(f"timesteps={ts}", sampler_override={"num_timesteps": ts})

    # Combined length + noise + step
    for length, noise, step in [
        (f"{center-10}-{center+10}", 0.9, 1.25),
        (f"{center-10}-{center+10}", 0.8, 1.5),
        (f"{center-20}-{center}", 1.0, 1.75),
        (f"{center}-{center+20}", 0.9, 1.5),
    ]:
        try_exp(f"L={length} noise={noise} step={step}",
                config_override={"length": length},
                sampler_override={"noise_scale": noise, "step_scale": step})

    # is_non_loopy toggle
    try_exp("loopy=true", config_override={"is_non_loopy": False})

    # COM orientation
    try_exp("ori=com", config_override={"infer_ori_strategy": "com"})

    # Final big batch
    try_exp("best_config x50 final", config_override={}, sampler_override={})

    log_msg(f"[{target_name}] === PHASE 4 COMPLETE ===")
    log_msg(f"[{target_name}] Best ipTM: {best_ever:.4f}")
    log_msg(f"[{target_name}] Config: {best_config}")
    log_msg(f"[{target_name}] Sampler: {best_sampler}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Single target")
    parser.add_argument("--gap-targets", action="store_true")
    parser.add_argument("--output-dir", default="analysis_output/autoresearch_phase4")
    parser.add_argument("--n-designs", type=int, default=20)
    args = parser.parse_args()
    if args.gap_targets:
        targets = ["HD", "PNRP1", "OCT4pt2", "HSTELO"]
    elif args.target:
        targets = [args.target]
    else:
        parser.error("Specify --target or --gap-targets")
    for t in targets:
        run_phase4(t, args.output_dir, args.n_designs)


if __name__ == "__main__":
    main()
