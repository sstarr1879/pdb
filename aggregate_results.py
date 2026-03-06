#!/usr/bin/env python3
"""
aggregate_results.py

Collects all experiment results from runs/ directory into a single CSV
and prints summary statistics by persona and question domain.

Usage:
    python aggregate_results.py
    python aggregate_results.py --runs-dir runs --output results.csv
"""

import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict


METRIC_FIELDS = [
    "word_count", "char_count", "sentence_count", "paragraph_count",
    "hedge_count", "refusal_count", "is_refusal",
    "specificity_hits", "hedge_density", "specificity_density",
    "response_time_s",
]

RECORD_FIELDS = [
    "timestamp", "persona_key", "persona_name", "question_key",
    "question_domain", "model", "run_id", "error",
] + METRIC_FIELDS


def load_results(runs_dir):
    """Load all results.jsonl files from run directories."""
    all_results = []
    for results_file in sorted(runs_dir.rglob("results.jsonl")):
        with open(results_file) as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    # Tag which run directory it came from
                    record["run_dir"] = str(results_file.parent.name)
                    all_results.append(record)
    return all_results


def avg(values):
    return round(sum(values) / len(values), 2) if values else 0


def print_pivot(results, row_key, row_label):
    """Print a pivot table showing metrics by row_key."""
    groups = defaultdict(list)
    for r in results:
        if not r.get("error"):
            groups[r[row_key]].append(r)

    print(f"\n{'=' * 80}")
    print(f"  BY {row_label.upper()}")
    print(f"{'=' * 80}")
    header = f"{'Key':<22} {'N':>4} {'AvgWords':>9} {'AvgHedge':>9} {'AvgSpec':>8} {'Refusals':>9}"
    print(header)
    print("-" * 80)

    for key in sorted(groups.keys()):
        recs = groups[key]
        n = len(recs)
        print(f"{key:<22} {n:>4} "
              f"{avg([r['word_count'] for r in recs]):>9} "
              f"{avg([r['hedge_count'] for r in recs]):>9} "
              f"{avg([r['specificity_hits'] for r in recs]):>8} "
              f"{sum(1 for r in recs if r.get('is_refusal')):>9}")


def main():
    parser = argparse.ArgumentParser(description="Aggregate PDB experiment results")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run results")
    parser.add_argument("--output", default="experiment_results.csv", help="Output CSV file")
    parser.add_argument("--json-output", default="experiment_results.json", help="Output JSON file")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        print(f"Error: {runs_dir} does not exist")
        return

    results = load_results(runs_dir)
    print(f"Loaded {len(results)} results")

    if not results:
        print("No results to process")
        return

    # Write CSV (without full response text to keep it manageable)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RECORD_FIELDS + ["run_dir"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {args.output}")

    # Write JSON with full responses for detailed analysis
    with open(args.json_output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {args.json_output}")

    # Summary tables
    valid = [r for r in results if not r.get("error")]
    print_pivot(valid, "persona_key", "Persona")
    print_pivot(valid, "question_key", "Question Domain")

    # Cross-tab: persona × question
    print(f"\n{'=' * 80}")
    print("  REFUSAL MATRIX (persona × question)")
    print(f"{'=' * 80}")
    question_keys = sorted(set(r["question_key"] for r in valid))
    persona_keys = sorted(set(r["persona_key"] for r in valid))

    header = f"{'Persona':<22}" + "".join(f"{q:>12}" for q in question_keys)
    print(header)
    print("-" * 80)

    for pk in persona_keys:
        row = f"{pk:<22}"
        for qk in question_keys:
            subset = [r for r in valid if r["persona_key"] == pk and r["question_key"] == qk]
            refusals = sum(1 for r in subset if r.get("is_refusal"))
            row += f"{refusals}/{len(subset):>10}"
        print(row)


if __name__ == "__main__":
    main()
