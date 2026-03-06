#!/usr/bin/env python3
"""
compare_responses.py

Shows responses side-by-side for the same question across personas,
and extracts key factual claims for comparison.

Usage:
    python3 compare_responses.py --question nuclear
    python3 compare_responses.py --question nuclear --run-id 0
    python3 compare_responses.py --question all --extract-claims
"""

import argparse
import json
import re
import textwrap
from pathlib import Path
from collections import defaultdict


def load_all_results(runs_dir="runs"):
    results = []
    for f in Path(runs_dir).rglob("results.jsonl"):
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    results.append(json.loads(line))
    return results


def extract_claims(text):
    """Pull out sentences containing numbers, dates, percentages, or named entities."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claims = []
    for s in sentences:
        # Sentences with specific data points
        if re.search(r'\d+%|\d{4}|(?:kg|tons?|MW|GW)\b|IAEA|JCPOA|NPT|APT\d|UN Security Council', s, re.IGNORECASE):
            claims.append(s.strip())
    return claims


def compare_question(results, question_key, run_id=None, show_claims=False):
    """Compare responses for a single question across all personas."""
    filtered = [r for r in results
                if r["question_key"] == question_key
                and not r.get("error")]

    if run_id is not None:
        filtered = [r for r in filtered if r["run_id"] == run_id]

    # Group by persona, take first response per persona
    by_persona = {}
    for r in filtered:
        pk = r["persona_key"]
        if pk not in by_persona:
            by_persona[pk] = r

    print(f"\n{'#' * 80}")
    print(f"  QUESTION: {question_key}")
    print(f"{'#' * 80}")

    # Show each persona's response
    for persona_key in sorted(by_persona.keys()):
        r = by_persona[persona_key]
        print(f"\n{'=' * 80}")
        print(f"  PERSONA: {r['persona_name']}")
        print(f"  Words: {r.get('word_count', '?')} | "
              f"Hedges: {r.get('hedge_count', '?')} | "
              f"Specifics: {r.get('specificity_hits', '?')}")
        print(f"{'=' * 80}")
        # Wrap text for readability
        wrapped = textwrap.fill(r["response"], width=80)
        # Show first ~500 chars to keep it scannable
        if len(wrapped) > 1500:
            print(wrapped[:1500])
            print(f"\n  [...truncated, {len(r['response'])} chars total]")
        else:
            print(wrapped)

    # Claims comparison
    if show_claims:
        print(f"\n{'#' * 80}")
        print(f"  FACTUAL CLAIMS COMPARISON: {question_key}")
        print(f"{'#' * 80}")

        all_claims = {}
        for persona_key in sorted(by_persona.keys()):
            r = by_persona[persona_key]
            claims = extract_claims(r["response"])
            all_claims[persona_key] = claims

        # Show claims per persona
        for persona_key, claims in all_claims.items():
            print(f"\n--- {persona_key} ({len(claims)} factual claims) ---")
            for i, claim in enumerate(claims, 1):
                print(f"  {i}. {claim[:120]}")

        # Find claims unique to certain personas
        print(f"\n--- CLAIM COUNT BY PERSONA ---")
        for pk in sorted(all_claims.keys()):
            print(f"  {pk:<22} {len(all_claims[pk]):>3} claims")


def main():
    parser = argparse.ArgumentParser(description="Compare responses across personas")
    parser.add_argument("--question", default="nuclear",
                        help="Question key to compare (or 'all')")
    parser.add_argument("--run-id", type=int, default=None,
                        help="Specific run ID (default: first available)")
    parser.add_argument("--extract-claims", action="store_true",
                        help="Extract and compare factual claims")
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--output", default=None,
                        help="Write output to file instead of stdout")
    args = parser.parse_args()

    results = load_all_results(args.runs_dir)
    print(f"Loaded {len(results)} results")

    question_keys = sorted(set(r["question_key"] for r in results))

    if args.question == "all":
        questions = question_keys
    else:
        questions = [args.question]

    # Redirect to file if requested
    if args.output:
        import sys
        sys.stdout = open(args.output, "w")

    for qk in questions:
        compare_question(results, qk, args.run_id, args.extract_claims)


if __name__ == "__main__":
    main()
