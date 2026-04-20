#!/usr/bin/env python3
"""Optuna-based parameter suggestion for binder autoresearch.

Reads previous results from a TSV file, builds an Optuna study,
and suggests the next parameter set to try.

Usage:
    # Get next suggested params for a target:
    python scripts/optuna_suggest.py --target HD --results analysis_output/autoresearch/HD_agent2.tsv

    # For TP53:
    python scripts/optuna_suggest.py --target TP53_tet --results analysis_output/tp53/tp53_results.tsv --tp53

Output: JSON with suggested parameters to use in the next experiment.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)


def load_previous_trials(results_tsv, is_tp53=False):
    """Load previous experiments as completed Optuna trials."""
    trials = []
    if not Path(results_tsv).exists():
        return trials
    with open(results_tsv) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            try:
                iptm = float(row.get("best_iptm") or row.get("iptm") or 0)
                if iptm <= 0:
                    continue
                change = row.get("change") or row.get("notes") or ""
                trials.append({"iptm": iptm, "change": change})
            except (ValueError, KeyError):
                continue
    return trials


def create_dna_study(trials):
    """Create Optuna study for DNA binder optimization."""
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))

    for t in trials:
        params = {}
        change = t["change"]
        # Parse known parameters from change description
        if "length=" in change:
            import re
            m = re.search(r"length=(\d+)-(\d+)", change)
            if m:
                params["length_lo"] = int(m.group(1))
                params["length_hi"] = int(m.group(2))
        if "CFG" in change or "cfg" in change:
            import re
            m = re.search(r"[Cc][Ff][Gg][_=]*(\d+\.?\d*)", change)
            if m:
                params["cfg_scale"] = float(m.group(1))
                params["use_cfg"] = True
        if "step" in change:
            import re
            m = re.search(r"step[_=]*(\d+\.?\d*)", change)
            if m:
                params["step_scale"] = float(m.group(1))
        if "noise" in change:
            import re
            m = re.search(r"noise[_=]*(\d+\.?\d*)", change)
            if m:
                params["noise_scale"] = float(m.group(1))
        if "gamma" in change:
            import re
            m = re.search(r"gamma[_=]*(\d+\.?\d*)", change)
            if m:
                params["gamma_0"] = float(m.group(1))
        if "ori" in change and "com" in change:
            params["ori_strategy"] = "com"
        if params:
            dist = _get_dna_distributions()
            trial_params = {}
            for k, v in params.items():
                if k in dist:
                    trial_params[k] = v
            if trial_params:
                try:
                    study.add_trial(
                        optuna.trial.create_trial(
                            params=trial_params,
                            distributions={k: dist[k] for k in trial_params},
                            values=[t["iptm"]],
                        )
                    )
                except Exception:
                    pass
    return study


def _get_dna_distributions():
    return {
        "length_lo": optuna.distributions.IntDistribution(50, 200, step=10),
        "length_hi": optuna.distributions.IntDistribution(70, 300, step=10),
        "use_cfg": optuna.distributions.CategoricalDistribution([True, False]),
        "cfg_scale": optuna.distributions.FloatDistribution(1.0, 3.0, step=0.5),
        "step_scale": optuna.distributions.FloatDistribution(1.0, 2.0, step=0.25),
        "noise_scale": optuna.distributions.FloatDistribution(0.8, 1.2, step=0.1),
        "gamma_0": optuna.distributions.FloatDistribution(0.0, 0.9, step=0.1),
        "ori_strategy": optuna.distributions.CategoricalDistribution(["none", "com", "hotspots"]),
    }


def suggest_dna_params(study):
    """Suggest next parameters for DNA binder."""
    dist = _get_dna_distributions()
    trial = study.ask(dist)
    length_lo = trial.params["length_lo"]
    length_hi = trial.params["length_hi"]
    if length_hi <= length_lo:
        length_hi = length_lo + 30

    result = {
        "length": f"{length_lo}-{length_hi}",
        "sampler_overrides": {},
    }
    if trial.params.get("use_cfg"):
        result["sampler_overrides"]["use_classifier_free_guidance"] = True
        result["sampler_overrides"]["cfg_scale"] = trial.params["cfg_scale"]
    if trial.params.get("step_scale", 1.0) != 1.0:
        result["sampler_overrides"]["step_scale"] = trial.params["step_scale"]
    if trial.params.get("noise_scale", 1.0) != 1.0:
        result["sampler_overrides"]["noise_scale"] = trial.params["noise_scale"]
    if trial.params.get("gamma_0", 0.0) > 0:
        result["sampler_overrides"]["gamma_0"] = trial.params["gamma_0"]
    ori = trial.params.get("ori_strategy", "none")
    if ori != "none":
        result["infer_ori_strategy"] = ori
    result["trial_number"] = trial.number
    return result


def create_tp53_study(trials):
    """Create Optuna study for TP53 binder optimization."""
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    # TP53 results have different format — each row is an individual design
    # Group by experiment and take the best per experiment
    best_by_exp = {}
    for t in trials:
        exp = t["change"]
        if exp not in best_by_exp or t["iptm"] > best_by_exp[exp]:
            best_by_exp[exp] = t["iptm"]
    return study


def suggest_tp53_params(study):
    dist = {
        "length": optuna.distributions.IntDistribution(12, 30, step=1),
        "use_cfg": optuna.distributions.CategoricalDistribution([True, False]),
        "cfg_scale": optuna.distributions.FloatDistribution(1.0, 3.0, step=0.5),
        "step_scale": optuna.distributions.FloatDistribution(1.0, 2.0, step=0.25),
        "noise_scale": optuna.distributions.FloatDistribution(0.8, 1.2, step=0.1),
        "gamma_0": optuna.distributions.FloatDistribution(0.0, 0.6, step=0.1),
    }
    trial = study.ask(dist)
    length = trial.params["length"]
    result = {
        "length": f"{length}-{length+5}",
        "sampler_overrides": {},
    }
    if trial.params.get("use_cfg"):
        result["sampler_overrides"]["use_classifier_free_guidance"] = True
        result["sampler_overrides"]["cfg_scale"] = trial.params["cfg_scale"]
    if trial.params.get("step_scale", 1.0) != 1.0:
        result["sampler_overrides"]["step_scale"] = trial.params["step_scale"]
    if trial.params.get("noise_scale", 1.0) != 1.0:
        result["sampler_overrides"]["noise_scale"] = trial.params["noise_scale"]
    if trial.params.get("gamma_0", 0.0) > 0:
        result["sampler_overrides"]["gamma_0"] = trial.params["gamma_0"]
    result["trial_number"] = trial.number
    return result


def main():
    parser = argparse.ArgumentParser(description="Optuna parameter suggestion for binder design")
    parser.add_argument("--target", required=True)
    parser.add_argument("--results", required=True, help="Path to results TSV")
    parser.add_argument("--tp53", action="store_true", help="Use TP53 parameter space")
    parser.add_argument("--n-suggestions", type=int, default=1)
    args = parser.parse_args()

    trials = load_previous_trials(args.results, is_tp53=args.tp53)
    print(f"Loaded {len(trials)} previous trials for {args.target}", file=sys.stderr)

    if args.tp53:
        study = create_tp53_study(trials)
        for _ in range(args.n_suggestions):
            suggestion = suggest_tp53_params(study)
            print(json.dumps(suggestion, indent=2))
    else:
        study = create_dna_study(trials)
        for _ in range(args.n_suggestions):
            suggestion = suggest_dna_params(study)
            print(json.dumps(suggestion, indent=2))


if __name__ == "__main__":
    main()
