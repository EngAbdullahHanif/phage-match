"""Exercise split and metric contracts using a simulated equipment audit."""

import argparse
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr
from sklearn.metrics import auc, average_precision_score, precision_recall_curve


FOLD_COUNT = 4
CUTOFFS = (1, 3, 5)
METHODS = ("training_prevalence", "simulated_scores")


def simulated_audit(rng):
    sites, devices = np.indices((24, 32)).reshape(2, -1)
    site_groups, device_groups = sites // 2, devices // 2
    expected = rng.uniform(0.05, 0.8, size=len(sites))
    category = rng.binomial(3, expected)
    label = category >= 2
    return sites, devices, site_groups, device_groups, expected, category, label


def make_splits(sites, devices, rng):
    def partition(groups):
        order = rng.permutation(np.unique(groups))
        assignment = {group: index % FOLD_COUNT for index, group in enumerate(order)}
        return np.array([assignment[group] for group in groups])

    row_fold = partition(np.arange(len(sites)))
    site_fold = partition(sites)
    device_fold = partition(devices)
    result = {}
    for name, values in (("random_pair", row_fold), ("leave_device_out", device_fold),
                         ("leave_site_out", site_fold)):
        result[name] = [(values != fold, values == fold) for fold in range(FOLD_COUNT)]
    result["doubly_blind"] = [
        ((site_fold != site) & (device_fold != device), (site_fold == site) & (device_fold == device))
        for site, device in itertools.product(range(FOLD_COUNT), repeat=2)
    ]
    return result


def audit_splits(name, folds, sites, devices):
    coverage = np.zeros(len(sites), dtype=int)
    for train, test in folds:
        if not train.any() or not test.any() or (train & test).any():
            raise ValueError(f"{name}: empty or overlapping split")
        for guarded_names, axis in ((("leave_site_out", "doubly_blind"), sites),
                                    (("leave_device_out", "doubly_blind"), devices)):
            if name in guarded_names and np.intersect1d(axis[train], axis[test]).size:
                raise ValueError(f"{name}: group overlap")
        coverage += test
    if not np.all(coverage == 1):
        raise ValueError(f"{name}: each row must be tested exactly once")


def ranking_metrics(labels, scores, devices):
    order = np.lexsort((devices, -scores))
    ranked = labels[order]
    count = ranked.sum()
    if not count:
        return None
    result = {f"recall_at_{k}": float(ranked[:k].sum() / count) for k in CUTOFFS}
    result["mrr"] = 1.0 / (np.flatnonzero(ranked)[0] + 1)
    return result


def classification_metrics(labels, scores):
    if len(np.unique(labels)) < 2:
        return {"auprc": None, "average_precision": None, "brier": float(np.mean((labels - scores) ** 2))}
    precision, recall, _ = precision_recall_curve(labels, scores)
    return {"auprc": float(auc(recall, precision)),
            "average_precision": float(average_precision_score(labels, scores)),
            "brier": float(np.mean((labels - scores) ** 2))}


def evaluate(sites, devices, category, labels, scores, fold_ids, rng, repeats):
    by_site = {}
    for site in np.unique(sites):
        rows = np.flatnonzero(sites == site)
        ranks = []
        for fold in np.unique(fold_ids[rows]):
            indices = rows[fold_ids[rows] == fold]
            metric = ranking_metrics(labels[indices], scores[indices], devices[indices])
            if metric is not None:
                ranks.append(metric)
        by_site[site] = rows, ranks

    def summarize(selected_sites):
        indices = np.concatenate([by_site[site][0] for site in selected_sites])
        ranks = [metric for site in selected_sites for metric in by_site[site][1]]
        values = classification_metrics(labels[indices], scores[indices])
        for key in (*[f"recall_at_{k}" for k in CUTOFFS], "mrr"):
            values[key] = float(np.mean([entry[key] for entry in ranks])) if ranks else None
        return values

    unique_sites = list(by_site)
    point = summarize(unique_sites)
    samples = [summarize(rng.choice(unique_sites, size=len(unique_sites), replace=True)) for _ in range(repeats)]
    intervals = {}
    for key in point:
        values = [sample[key] for sample in samples if sample[key] is not None]
        intervals[key] = {"bounds": np.quantile(values, [0.025, 0.975]).tolist() if values else None,
                          "valid_replicates": len(values)}
    bins = np.minimum((scores * 10).astype(int), 9)
    reliability = [{"bin": number, "count": int(mask.sum()), "mean_score": float(scores[mask].mean()),
                    "observed_rate": float(labels[mask].mean())}
                   for number in range(10) if (mask := bins == number).any()]
    rho = None if np.unique(scores).size < 2 else float(spearmanr(category, scores).statistic)
    return {"metrics": point, "site_bootstrap_95": intervals, "reliability": reliability,
            "exploratory_category_spearman": rho}


def run(seed, repeats):
    rng = np.random.default_rng(seed)
    sites, devices, site_groups, device_groups, scores, category, label = simulated_audit(rng)
    results = {}
    for name, folds in make_splits(site_groups, device_groups, rng).items():
        audit_splits(name, folds, site_groups, device_groups)
        fold_ids = np.empty(len(label), dtype=int)
        prevalence = np.empty(len(label))
        split_counts = []
        for index, (train, test) in enumerate(folds):
            if np.unique(label[train]).size != 2:
                raise ValueError(f"{name}: training fold {index} lacks a class")
            prevalence[test] = label[train].mean()
            fold_ids[test] = index
            split_counts.append({"train": int(train.sum()), "test": int(test.sum()),
                                 "excluded": int((~(train | test)).sum())})
        results[name] = {"fold_counts": split_counts, **{
            method: evaluate(sites, devices, category, label, estimate, fold_ids, rng, repeats)
            for method, estimate in zip(METHODS, (prevalence, scores))
        }}
    return results


def write_report(path, results, revision, run_id):
    lines = ["# Synthetic evaluation audit", "",
             "This is an equipment-event simulation. Metrics verify evaluation behavior and carry no biological or clinical interpretation.",
             "", f"Run `{run_id}` used Git revision `{revision}`.", "",
             "| Split | Scores | PR AUC | Average precision | Recall@1 | Recall@3 | Recall@5 | MRR | Brier |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    keys = ("auprc", "average_precision", "recall_at_1", "recall_at_3", "recall_at_5", "mrr", "brier")
    for name, values in results.items():
        for method in METHODS:
            result = values[method]
            cells = [name, method]
            for key in keys:
                point = result["metrics"][key]
                interval = result["site_bootstrap_95"][key]["bounds"]
                cells.append(f"{point:.3f} [{interval[0]:.3f}, {interval[1]:.3f}]" if interval else "—")
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "Brackets show 95% percentile intervals from resampling sites with fixed out-of-fold scores.",
              "Ranking metrics average across site-fold groups that contain a positive. Exact ties use device ID order.",
              "The JSON also records reliability bins, fold sizes, and exploratory category rank correlations.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="Parent directory for run artifacts")
    parser.add_argument("--seed", type=int, default=315)
    parser.add_argument("--bootstrap", type=int, default=200)
    args = parser.parse_args()
    if args.bootstrap < 1 or args.seed < 0:
        parser.error("Use a positive bootstrap count and a nonnegative seed")
    root = Path(__file__).resolve().parents[1]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    results = run(args.seed, args.bootstrap)
    output = args.output_dir / run_id
    output.mkdir(parents=True, exist_ok=False)
    config = {"dataset": "simulated_equipment_events", "seed": args.seed, "bootstrap": args.bootstrap,
              "fold_count_per_axis": FOLD_COUNT, "git_sha": revision}
    (output / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    (output / "metrics.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_report(output / "synthetic_evaluation.md", results, revision, run_id)
    print(output)


if __name__ == "__main__":
    main()
