#!/bin/bash
#
# batch_experiments.sh
#
# Submit multiple experiment jobs to SLURM, one per model.
# Each job runs all personas × all questions.
#
# Usage:
#     bash batch_experiments.sh
#     RUNS=5 bash batch_experiments.sh

set -euo pipefail

RUNS="${RUNS:-3}"

MODELS=(
    "llama3.1:8b"
    "llama3.2:1b"
    "mistral:7b"
)

for MODEL in "${MODELS[@]}"; do
    echo "Submitting job for model: $MODEL (${RUNS} runs per pair)"
    sbatch \
        --export=ALL,OLLAMA_MODEL="$MODEL",RUNS="$RUNS" \
        experiment.sbatch
done

echo "All jobs submitted. Check queue with: squeue -u \$USER"
