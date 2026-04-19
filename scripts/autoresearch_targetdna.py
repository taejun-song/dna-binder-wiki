#!/usr/bin/env python3
"""Autoresearch with target-specific DNA templates.

Uses per-target ideal B-DNA PDBs instead of generic 1BNA.
Runs the best parameters found from Phase 3 autoresearch as baseline,
then explores further with the new DNA template.

Usage:
    python scripts/autoresearch_targetdna.py --target HD
    python scripts/autoresearch_targetdna.py --all-targets
"""
import argparse
import copy
import gzip
import json
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}

BEST_PARAMS = {
    "HD": {"config": {"length": "110-130"}, "sampler": {}},
    "PNRP1": {"config": {"length": "250-300"}, "sampler": {"use_classifier_free_guidance": True, "cfg_scale": 1.5, "num_timesteps": 200}},
    "OCT4pt2": {"config": {"length": "120-140"}, "sampler": {"gamma_0": 0.3}},
    "HSTELO": {"config": {"length": "140-180"}, "sampler": {}},
    "NFKB": {"config": {"length": "80-120"}, "sampler": {}},
    "OCT4pt1": {"config": {"length": "140-180", "infer_ori_strategy": "com"}, "sampler": {"step_scale": 1.25, "noise_scale": 0.9}},
    "CAG": {"config": {"length": "120-140"}, "sampler": {"noise_scale": 0.9, "gamma_0": 0.0}},
    "TATA": {"config": {"length": "180-220"}, "sampler": {}},
    "Dux4grna2": {"config": {"length": "220-260", "infer_ori_strategy": "com"}, "sampler": {}},
}

AA3TO1 = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G", "HIS": "H",
    "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q",
    "ARG": "R", "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
}
BIN_DIR = Path(sys.executable).parent
CKPT = Path.home() / ".foundry/checkpoints/rfd3_latest.ckpt"


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
    n = len(seq)
    b_start = n + 1
    b_end = b_start + n - 1
    return f"A1-{n},/0,B{b_start}-{b_end},/0,{length_range}"


def run_experiment(target_name, config_overrides, sampler_overrides, exp_dir, n_designs=10):
    exp_dir = Path(exp_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)
    rfd3_out = exp_dir / "rfd3_output"

    dna_pdb = Path(f"data/dna_templates/{target_name}.pdb").resolve()
    if not dna_pdb.exists():
        dna_pdb = Path("data/dna_templates/1BNA.pdb").resolve()
        log_msg(f"WARNING: {target_name}.pdb not found, falling back to 1BNA")

    length_range = config_overrides.pop("length", "120-140")
    contig = get_contig(target_name, length_range)

    config = {
        "design": {
            "input": str(dna_pdb),
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
    result = subprocess.run(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT, timeout=900)

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
    results_file = base_dir / f"{target_name}_targetdna.tsv"

    def log_result(exp_id, change, best_iptm, mean_iptm, best_ptm, n_scored, status):
        write_header = not results_file.exists() or results_file.stat().st_size == 0
        with open(results_file, "a") as f:
            if write_header:
                f.write("timestamp\texperiment\ttarget\tchange\tn_scored\tbest_iptm\tmean_iptm\tbest_ptm\tstatus\n")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts}\t{exp_id}\t{target_name}\t{change}\t{n_scored}\t{best_iptm:.4f}\t{mean_iptm:.4f}\t{best_ptm:.4f}\t{status}\n")

    prev = BEST_PARAMS.get(target_name, {"config": {}, "sampler": {}})
    best_config = copy.deepcopy(prev["config"])
    best_sampler = copy.deepcopy(prev["sampler"])
    best_ever = 0.0
    exp_count = 0

    # Phase 1: Baseline with target-specific DNA + previous best params
    exp_count += 1
    exp_id = f"tdna{exp_count:03d}"
    change = f"target-DNA + prev best params"
    log_msg(f"[{target_name}] {exp_id}: {change}")
    iptm, mean, ptm, n = run_experiment(
        target_name, copy.deepcopy(best_config), copy.deepcopy(best_sampler),
        base_dir / target_name / exp_id, n_designs
    )
    if iptm > best_ever:
        best_ever = iptm
    log_result(exp_id, change, iptm, mean, ptm, n, "baseline")
    log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} mean={mean:.4f} -> baseline")

    # Phase 2: Length re-sweep (DNA shape may change optimal length)
    for length in ["80-120", "100-140", "110-130", "120-160", "140-180", "160-200", "180-220"]:
        exp_count += 1
        exp_id = f"tdna{exp_count:03d}"
        change = f"length={length}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        cfg = copy.deepcopy(best_config)
        cfg["length"] = length
        iptm, mean, ptm, n = run_experiment(
            target_name, cfg, copy.deepcopy(best_sampler),
            base_dir / target_name / exp_id, n_designs
        )
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_config["length"] = length
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 3: CFG sweep
    for cfg_scale in [1.0, 1.5, 2.0, 2.5]:
        exp_count += 1
        exp_id = f"tdna{exp_count:03d}"
        change = f"CFG={cfg_scale}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        sampler = copy.deepcopy(best_sampler)
        sampler["use_classifier_free_guidance"] = True
        sampler["cfg_scale"] = cfg_scale
        iptm, mean, ptm, n = run_experiment(
            target_name, copy.deepcopy(best_config), sampler,
            base_dir / target_name / exp_id, n_designs
        )
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_sampler = sampler
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 4: Noise + gamma
    for noise, gamma in [(0.8, 0.0), (0.9, 0.0), (1.0, 0.3), (0.9, 0.3), (1.1, 0.0)]:
        exp_count += 1
        exp_id = f"tdna{exp_count:03d}"
        change = f"noise={noise} gamma={gamma}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        sampler = copy.deepcopy(best_sampler)
        sampler["noise_scale"] = noise
        sampler["gamma_0"] = gamma
        iptm, mean, ptm, n = run_experiment(
            target_name, copy.deepcopy(best_config), sampler,
            base_dir / target_name / exp_id, n_designs
        )
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_sampler["noise_scale"] = noise
            best_sampler["gamma_0"] = gamma
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 5: Orientation
    for ori in ["com", "hotspots"]:
        exp_count += 1
        exp_id = f"tdna{exp_count:03d}"
        change = f"ori={ori}"
        log_msg(f"[{target_name}] {exp_id}: {change}")
        cfg = copy.deepcopy(best_config)
        cfg["infer_ori_strategy"] = ori
        iptm, mean, ptm, n = run_experiment(
            target_name, cfg, copy.deepcopy(best_sampler),
            base_dir / target_name / exp_id, n_designs
        )
        status = "keep" if iptm > best_ever else "discard"
        if iptm > best_ever:
            best_ever = iptm
            best_config["infer_ori_strategy"] = ori
            log_msg(f"[{target_name}] NEW BEST: ipTM={iptm:.4f}")
        log_result(exp_id, change, iptm, mean, ptm, n, status)
        log_msg(f"[{target_name}] {exp_id}: ipTM={iptm:.4f} -> {status}")

    # Phase 6: Final big batch
    exp_count += 1
    exp_id = f"tdna{exp_count:03d}"
    change = "best_config x50"
    log_msg(f"[{target_name}] {exp_id}: {change}")
    iptm, mean, ptm, n = run_experiment(
        target_name, copy.deepcopy(best_config), copy.deepcopy(best_sampler),
        base_dir / target_name / exp_id, 50
    )
    log_result(exp_id, change, iptm, mean, ptm, n, "final")
    if iptm > best_ever:
        best_ever = iptm

    log_msg(f"[{target_name}] === TARGET-DNA AUTORESEARCH COMPLETE ===")
    log_msg(f"[{target_name}] Best ipTM: {best_ever:.4f}")
    log_msg(f"[{target_name}] Best config: {best_config}")
    log_msg(f"[{target_name}] Best sampler: {best_sampler}")
    return best_ever, best_config, best_sampler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Single target")
    parser.add_argument("--all-targets", action="store_true")
    parser.add_argument("--gap-targets", action="store_true", help="Only targets trailing Baker Lab")
    parser.add_argument("--output-dir", default="analysis_output/autoresearch_targetdna")
    parser.add_argument("--n-designs", type=int, default=10)
    args = parser.parse_args()

    if args.gap_targets:
        targets = ["HD", "PNRP1", "OCT4pt2", "HSTELO"]
    elif args.all_targets:
        targets = list(TARGETS.keys())
    elif args.target:
        targets = [args.target]
    else:
        parser.error("Specify --target, --all-targets, or --gap-targets")

    for target in targets:
        log_msg(f"Starting target-DNA autoresearch for {target}")
        run_autoresearch(target, args.output_dir, args.n_designs)


if __name__ == "__main__":
    main()
