#!/usr/bin/env python3
"""Overnight autonomous runner: generate binders + score, monitoring GPU VRAM.

Runs until interrupted. Logs all results to results.tsv.
"""
import json
import gzip
import subprocess
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

TARGETS = {
    "PNRP1": "TGAGGAGAGGAG", "CAG": "CAGCAGCAGCAG", "HSTELO": "AGGGTTAGGGTT",
    "OCT4pt1": "GGTGAAATGA", "OCT4pt2": "GGGCTTGCGA", "NFKB": "GGGGATTCCCCC",
    "HD": "GCTTAATTAGCG", "TATA": "CGTATAAACG", "Dux4grna2": "CAGGCCGCAGG",
}
AA3TO1 = {
    "ALA":"A","CYS":"C","ASP":"D","GLU":"E","PHE":"F","GLY":"G","HIS":"H",
    "ILE":"I","LYS":"K","LEU":"L","MET":"M","ASN":"N","PRO":"P","GLN":"Q",
    "ARG":"R","SER":"S","THR":"T","VAL":"V","TRP":"W","TYR":"Y",
}
CKPT = Path.home() / ".foundry/checkpoints/rfd3_latest.ckpt"
RF3_CKPT = Path.home() / ".foundry/checkpoints/rf3_foundry_01_24_latest_remapped.ckpt"
VRAM_RESERVE_MB = 15000
BIN_DIR = Path(sys.executable).parent
BASE_DIR = Path("analysis_output/overnight")
CONFIGS_DIR = Path("data/rfd3_configs")
RESULTS_TSV = BASE_DIR / "results.tsv"


def get_gpu_free_mb():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            text=True,
        )
        return int(out.strip().split("\n")[0])
    except Exception:
        return 0


def get_gpu_used_mb():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
        )
        return int(out.strip().split("\n")[0])
    except Exception:
        return 999999


def count_processes(pattern):
    try:
        out = subprocess.check_output(f"ps aux | grep '{pattern}' | grep -v grep | wc -l", shell=True, text=True)
        return int(out.strip())
    except Exception:
        return 0


def extract_seq(cif_path):
    residues = OrderedDict()
    opener = gzip.open if str(cif_path).endswith(".gz") else open
    with opener(cif_path, "rt") as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            parts = line.split()
            if len(parts) < 12:
                continue
            if parts[2] == "CA" and parts[4] in AA3TO1:
                key = (parts[5], parts[7])
                if key not in residues:
                    residues[key] = AA3TO1[parts[4]]
    return "".join(residues.values())


def launch_rfd3(target_name, batch_id, n_batches=25):
    config_path = CONFIGS_DIR / f"{target_name}_config.json"
    if not config_path.exists():
        return None
    out_dir = BASE_DIR / f"{target_name}_b{batch_id}" / "rfd3_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir.parent / "rfd3.log"
    cmd = [
        str(BIN_DIR / "rfd3"),
        f"out_dir={out_dir}",
        f"inputs={config_path.resolve()}",
        f"n_batches={n_batches}",
        f"ckpt_path={CKPT}",
    ]
    proc = subprocess.Popen(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT)
    return proc


def score_batch(target_name, batch_dir, dna_seq):
    cif_files = sorted(batch_dir.glob("rfd3_output/*.cif.gz"))
    if not cif_files:
        return []
    rf3_inputs = []
    for cif in cif_files:
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
        return []
    score_dir = batch_dir / "rf3_scoring"
    score_dir.mkdir(exist_ok=True)
    input_path = score_dir / "rf3_inputs.json"
    with open(input_path, "w") as f:
        json.dump(rf3_inputs, f)
    results_dir = score_dir / "results"
    log_path = score_dir / "rf3.log"
    cmd = [
        str(BIN_DIR / "rf3"), "fold",
        f"inputs={input_path}",
        f"out_dir={results_dir}",
    ]
    subprocess.run(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT)
    scores = []
    for inp in rf3_inputs:
        summary_files = list(results_dir.rglob(f"*{inp['name']}*summary_confidences*"))
        if summary_files:
            with open(summary_files[0]) as f:
                data = json.load(f)
            scores.append({
                "name": inp["name"],
                "target": target_name,
                "ptm": data.get("ptm", 0.0),
                "iptm": data.get("iptm", 0.0),
                "ranking_score": data.get("ranking_score", 0.0),
            })
    return scores


def log_scores(scores):
    write_header = not RESULTS_TSV.exists()
    with open(RESULTS_TSV, "a") as f:
        if write_header:
            f.write("timestamp\ttarget\tname\tptm\tiptm\tranking_score\n")
        for s in scores:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts}\t{s['target']}\t{s['name']}\t{s['ptm']:.4f}\t{s['iptm']:.4f}\t{s['ranking_score']:.4f}\n")


def log_msg(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    target_list = list(TARGETS.keys())
    batch_counter = {t: 0 for t in target_list}
    active_rfd3 = {}  # batch_key -> (proc, target_name)
    pending_score = []  # (target_name, batch_dir)
    total_scored = 0
    best_iptm = {t: 0.0 for t in target_list}

    log_msg(f"Overnight runner started. {len(target_list)} targets. VRAM reserve: {VRAM_RESERVE_MB}MB")
    log_msg(f"Results: {RESULTS_TSV}")

    target_idx = 0
    while True:
        free_mb = get_gpu_free_mb()
        n_rfd3 = count_processes("rfd3.*ckpt")
        n_rf3 = count_processes("rf3 fold")

        # Check completed RFD3 processes
        done_keys = []
        for key, (proc, tname) in active_rfd3.items():
            if proc.poll() is not None:
                batch_dir = BASE_DIR / key
                cif_count = len(list((batch_dir / "rfd3_output").glob("*.cif.gz")))
                log_msg(f"RFD3 done: {key} -> {cif_count} CIFs")
                if cif_count > 0:
                    pending_score.append((tname, batch_dir))
                done_keys.append(key)
        for key in done_keys:
            del active_rfd3[key]

        # Score pending batches if GPU has room
        if pending_score and free_mb > VRAM_RESERVE_MB and n_rf3 < 3:
            tname, batch_dir = pending_score.pop(0)
            dna_seq = TARGETS[tname]
            log_msg(f"RF3 scoring: {batch_dir.name} ({tname})")
            scores = score_batch(tname, batch_dir, dna_seq)
            if scores:
                log_scores(scores)
                total_scored += len(scores)
                for s in scores:
                    if s["iptm"] > best_iptm[s["target"]]:
                        best_iptm[s["target"]] = s["iptm"]
                        log_msg(f"NEW BEST {s['target']}: ipTM={s['iptm']:.4f} ({s['name']})")
                log_msg(f"Scored {len(scores)} complexes. Total scored: {total_scored}")

        # Launch new RFD3 if GPU has room
        elif free_mb > VRAM_RESERVE_MB + 8000 and len(active_rfd3) < 6:
            tname = target_list[target_idx % len(target_list)]
            target_idx += 1
            batch_counter[tname] += 1
            batch_key = f"{tname}_b{batch_counter[tname]}"
            log_msg(f"Launching RFD3: {batch_key} (free={free_mb}MB, active={len(active_rfd3)})")
            proc = launch_rfd3(tname, batch_counter[tname], n_batches=25)
            if proc:
                active_rfd3[batch_key] = (proc, tname)
            time.sleep(5)
            continue

        # Status report every cycle
        if len(active_rfd3) == 0 and len(pending_score) == 0 and n_rfd3 == 0 and n_rf3 == 0:
            log_msg(f"Idle. Launching new batch... (total scored: {total_scored})")
            continue

        time.sleep(30)


if __name__ == "__main__":
    main()
