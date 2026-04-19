#!/usr/bin/env python3
"""Autoresearch loop for RFD3 DNA binder parameter optimization.

Sweeps RFD3 parameters per target, scores with RF3, keeps improvements.
Inspired by Karpathy's autoresearch framework.

Usage:
    python scripts/autoresearch_binder.py --target PNRP1
    python scripts/autoresearch_binder.py --all-targets
"""
import argparse
import copy
import csv
import gzip
import json
import subprocess
import sys
import time
from collections import OrderedDict
from datetime import datetime
from itertools import product
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
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


def run_experiment(target_name, config_overrides, sampler_overrides, exp_dir, n_designs=10):
    """Run one RFD3 experiment and score with RF3. Returns best_iptm, mean_iptm, best_ptm."""
    exp_dir = Path(exp_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)
    rfd3_out = exp_dir / "rfd3_output"

    length_range = config_overrides.pop("length", "120-140")
    contig = get_contig(target_name, length_range)

    config = {
        "design": {
            "input": str(DNA_PDB),
            "contig": contig,
            "is_non_loopy": config_overrides.get("is_non_loopy", True),
        }
    }
    for k, v in config_overrides.items():
        if k not in ("length", "is_non_loopy"):
            config["design"][k] = v

    config_path = exp_dir / "config.json"
    config_path.write_text(json.dumps(config))

    cmd = [
        str(BIN_DIR / "rfd3"),
        f"out_dir={rfd3_out}",
        f"inputs={config_path}",
        f"n_batches={n_designs}",
        f"ckpt_path={CKPT}",
    ]
    for k, v in sampler_overrides.items():
        if isinstance(v, bool):
            v = str(v).lower()
        cmd.append(f"inference_sampler.{k}={v}")

    log_path = exp_dir / "rfd3.log"
    result = subprocess.run(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT, timeout=600)

    cifs = sorted(rfd3_out.rglob("*.cif.gz")) if rfd3_out.exists() else []
    if not cifs:
        return 0.0, 0.0, 0.0, 0

    dna_seq = TARGETS[target_name]
    rf3_inputs = []
    for cif in cifs:
        seq = extract_seq(cif)
        if seq and len(seq) >= 50:
            rf3_inputs.append({
                "name": cif.stem.replace(".cif", ""),
                "components": [
                    {"seq": seq, "chain_id": "A"},
                    {"seq": dna_seq, "chain_id": "B"},
                ],
            })
    if not rf3_inputs:
        return 0.0, 0.0, 0.0, 0

    rf3_dir = exp_dir / "rf3"
    rf3_dir.mkdir(exist_ok=True)
    input_path = rf3_dir / "inputs.json"
    input_path.write_text(json.dumps(rf3_inputs))

    rf3_cmd = [str(BIN_DIR / "rf3"), "fold", f"inputs={input_path}", f"out_dir={rf3_dir}/results"]
    subprocess.run(rf3_cmd, stdout=open(rf3_dir / "rf3.log", "w"), stderr=subprocess.STDOUT, timeout=1800)

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


def run_autoresearch(target_name, base_dir, n_designs=10):
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    results_file = base_dir / f"{target_name}_autoresearch.tsv"

    write_header = not results_file.exists()
    def log_result(exp_id, change, best_iptm, mean_iptm, best_ptm, n_scored, status):
        with open(results_file, "a") as f:
            if write_header and f.tell() == 0:
                f.write("timestamp\texperiment\ttarget\tchange\tn_scored\tbest_iptm\tmean_iptm\tbest_ptm\tstatus\n")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts}\t{exp_id}\t{target_name}\t{change}\t{n_scored}\t{best_iptm:.4f}\t{mean_iptm:.4f}\t{best_ptm:.4f}\t{status}\n")

    best_ever = 0.0
    best_config = {}
    best_sampler = {}
    exp_count = 0

    # Phase 1: Baseline
    exp_count += 1
    exp_id = f"exp{exp_count:03d}"
    log_msg(f"[{target_name}] {exp_id}: baseline length=120-140")
    iptm, mean, ptm, n = run_experiment(target_name, {"length": "120-140"}, {}, base_dir / target_name / exp_id, n_designs)
    status = "keep" if iptm > best_ever else "discard"
    if iptm > best_ever:
        best_ever = iptm
        best_config = {"length": "120-140"}
    log_result(exp_id, "baseline length=120-140", iptm, mean, ptm, n, status)
    log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} mean={mean:.4f} pTM={ptm:.4f} -> {status}")

    # Phase 2: Length sweep
    for length in ["50-80", "60-90", "70-100", "80-120", "100-140", "140-180", "160-200", "100-120", "130-150"]:
        exp_count += 1
        exp_id = f"exp{exp_count:03d}"
        change = f"length={length}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        cfg = copy.deepcopy(best_config)
        cfg["length"] = length
        iptm, mean, ptm, n = run_experiment(target_name, cfg, best_sampler, base_dir / target_name / exp_id, n_designs)
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_config["length"] = length
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 3: Classifier-free guidance
    for cfg_scale in [1.0, 1.5, 2.0, 2.5, 3.0]:
        exp_count += 1
        exp_id = f"exp{exp_count:03d}"
        change = f"CFG scale={cfg_scale}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        sampler = {"use_classifier_free_guidance": True, "cfg_scale": cfg_scale}
        iptm, mean, ptm, n = run_experiment(target_name, copy.deepcopy(best_config), sampler, base_dir / target_name / exp_id, n_designs)
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_sampler = sampler
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 4: Step scale
    for step_scale in [1.0, 1.25, 1.75, 2.0]:
        exp_count += 1
        exp_id = f"exp{exp_count:03d}"
        change = f"step_scale={step_scale}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        sampler = copy.deepcopy(best_sampler)
        sampler["step_scale"] = step_scale
        iptm, mean, ptm, n = run_experiment(target_name, copy.deepcopy(best_config), sampler, base_dir / target_name / exp_id, n_designs)
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_sampler["step_scale"] = step_scale
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 5: Noise scale + gamma
    for noise_scale, gamma_0 in product([0.8, 1.0, 1.1], [0.0, 0.3, 0.6]):
        exp_count += 1
        exp_id = f"exp{exp_count:03d}"
        change = f"noise={noise_scale} gamma={gamma_0}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        sampler = copy.deepcopy(best_sampler)
        sampler["noise_scale"] = noise_scale
        sampler["gamma_0"] = gamma_0
        iptm, mean, ptm, n = run_experiment(target_name, copy.deepcopy(best_config), sampler, base_dir / target_name / exp_id, n_designs)
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_sampler["noise_scale"] = noise_scale
            best_sampler["gamma_0"] = gamma_0
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 6: Topology + orientation
    for is_non_loopy in [True, False]:
        for ori_strategy in [None, "com", "hotspots"]:
            exp_count += 1
            exp_id = f"exp{exp_count:03d}"
            change = f"loopy={not is_non_loopy} ori={ori_strategy}"
            log_msg(f"[{target_name}] {exp_id}: {change}")
            cfg = copy.deepcopy(best_config)
            cfg["is_non_loopy"] = is_non_loopy
            if ori_strategy:
                cfg["infer_ori_strategy"] = ori_strategy
            iptm, mean, ptm, n = run_experiment(target_name, cfg, copy.deepcopy(best_sampler), base_dir / target_name / exp_id, n_designs)
            status = "keep" if iptm > best_ever else "discard"
            if iptm > best_ever:
                best_ever = iptm
                best_config["is_non_loopy"] = is_non_loopy
                if ori_strategy:
                    best_config["infer_ori_strategy"] = ori_strategy
                log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
            log_result(exp_id, change, iptm, mean, ptm, n, status)
            log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 7: Best config with more designs
    exp_count += 1
    exp_id = f"exp{exp_count:03d}"
    change = "best_config x50"
    log_msg(f"[{target_name}] {exp_id}: {change} — generating 50 with best params")
    iptm, mean, ptm, n = run_experiment(target_name, copy.deepcopy(best_config), copy.deepcopy(best_sampler), base_dir / target_name / exp_id, 50)
    log_result(exp_id, change, iptm, mean, ptm, n, "final")
    log_msg(f"[{target_name}] FINAL: ipTM={iptm:.4f} mean={mean:.4f} pTM={ptm:.4f}")

    log_msg(f"[{target_name}] === AUTORESEARCH COMPLETE ===")
    log_msg(f"[{target_name}] Best ipTM: {best_ever:.4f}")
    log_msg(f"[{target_name}] Best config: {best_config}")
    log_msg(f"[{target_name}] Best sampler: {best_sampler}")
    log_msg(f"[{target_name}] Total experiments: {exp_count}")

    return best_ever, best_config, best_sampler


def main():
    parser = argparse.ArgumentParser(description="Autoresearch for RFD3 DNA binder parameters")
    parser.add_argument("--target", help="Single target to optimize")
    parser.add_argument("--all-targets", action="store_true", help="Optimize all targets sequentially")
    parser.add_argument("--output-dir", default="analysis_output/autoresearch")
    parser.add_argument("--n-designs", type=int, default=10, help="Designs per experiment")
    args = parser.parse_args()

    if args.all_targets:
        targets = list(TARGETS.keys())
    elif args.target:
        targets = [args.target]
    else:
        parser.error("Specify --target or --all-targets")

    for target in targets:
        log_msg(f"Starting autoresearch for {target}")
        best_iptm, best_config, best_sampler = run_autoresearch(target, args.output_dir, args.n_designs)
        log_msg(f"Done: {target} best_ipTM={best_iptm:.4f}")


if __name__ == "__main__":
    main()
