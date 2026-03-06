#!/usr/bin/env python3
"""
experiment.py

Main experiment loop for the intelligence briefing persona experiment.
Runs all persona × question combinations and logs structured results.

Usage:
    # Run all personas × all questions, 3 runs each (default)
    python experiment.py

    # Specific persona and question
    python experiment.py --persona senior_analyst --question nuclear --runs 5

    # Specify model
    OLLAMA_MODEL=llama3.2:1b python experiment.py

    # Use OpenAI backend
    LLM_BACKEND=openai python experiment.py --model gpt-4o-mini
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from api_calls import call_llm
from metrics import extract_metrics
from personas import PERSONAS
from questions import QUESTIONS


def build_user_prompt(question_text: str) -> str:
    """Wrap the question in a briefing-request frame."""
    return (
        "I need a briefing on the following topic. Provide a thorough, "
        "factual assessment.\n\n"
        f"{question_text}"
    )


def run_single(persona_key, question_key, model, run_id):
    """Execute one persona × question call and return structured result."""
    persona = PERSONAS[persona_key]
    question = QUESTIONS[question_key]

    system_prompt = persona["system_prompt"]
    user_prompt = build_user_prompt(question["question"])

    start = time.time()
    try:
        response = call_llm(system_prompt, user_prompt, model=model)
        elapsed = time.time() - start
        error = None
    except Exception as e:
        response = ""
        elapsed = time.time() - start
        error = str(e)

    result_metrics = extract_metrics(response) if response else {}

    return {
        "timestamp": datetime.now().isoformat(),
        "persona_key": persona_key,
        "persona_name": persona["name"],
        "question_key": question_key,
        "question_domain": question["domain"],
        "model": model or os.environ.get("OLLAMA_MODEL", "default"),
        "run_id": run_id,
        "response": response,
        "response_time_s": round(elapsed, 2),
        "error": error,
        **result_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Intelligence Briefing Persona Experiment")
    parser.add_argument("--persona", type=str, default=None,
                        help="Specific persona key to test (default: all)")
    parser.add_argument("--question", type=str, default=None,
                        help="Specific question key to test (default: all)")
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of runs per persona×question pair")
    parser.add_argument("--model", type=str, default=None,
                        help="Model override (otherwise uses env defaults)")
    parser.add_argument("--output-dir", type=str, default="runs",
                        help="Output directory")
    args = parser.parse_args()

    # Determine which personas and questions to run
    persona_keys = [args.persona] if args.persona else list(PERSONAS.keys())
    question_keys = [args.question] if args.question else list(QUESTIONS.keys())

    # Create run output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_tag = (args.model or os.environ.get("OLLAMA_MODEL", "default")).replace(":", "-")
    run_dir = Path(args.output_dir) / f"{timestamp}_{model_tag}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save experiment config
    config = {
        "personas": persona_keys,
        "questions": question_keys,
        "runs_per_pair": args.runs,
        "model": args.model or os.environ.get("OLLAMA_MODEL", "default"),
        "backend": os.environ.get("LLM_BACKEND", "ollama"),
        "timestamp": timestamp,
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Run experiment
    results_file = run_dir / "results.jsonl"
    total = len(persona_keys) * len(question_keys) * args.runs
    completed = 0

    with open(results_file, "w") as f:
        for question_key in question_keys:
            for persona_key in persona_keys:
                for run_id in range(args.runs):
                    completed += 1
                    print(f"[{completed}/{total}] {persona_key} × {question_key} (run {run_id})")

                    result = run_single(persona_key, question_key, args.model, run_id)
                    f.write(json.dumps(result) + "\n")
                    f.flush()

                    if result["error"]:
                        print(f"  ERROR: {result['error']}")
                    else:
                        print(f"  {result['word_count']} words, "
                              f"{result['hedge_count']} hedges, "
                              f"{result['specificity_hits']} specifics, "
                              f"refusal={result['is_refusal']}")

    print(f"\nDone. Results written to {results_file}")
    print(f"Total calls: {completed}")


if __name__ == "__main__":
    main()
