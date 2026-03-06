#!/bin/bash
#SBATCH --job-name=pdb-intel
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

# ── tunables (override via environment) ──────────────────────────────────
MODEL="${OLLAMA_MODEL:-llama3.1:70b}"
OLLAMA_SERVER="http://localhost:11434"
PERSONA="${PERSONA:-}"          # empty = all personas
QUESTION="${QUESTION:-}"        # empty = all questions
RUNS="${RUNS:-3}"
# ─────────────────────────────────────────────────────────────────────────

echo "=== PDB Intelligence Briefing Experiment ==="
echo "Model:    $MODEL"
echo "Persona:  ${PERSONA:-all}"
echo "Question: ${QUESTION:-all}"
echo "Runs:     $RUNS"
echo "============================================="

# ── environment ──────────────────────────────────────────────────────────
module load apptainer 2>/dev/null || true
source ~/venvs/pdb/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true

# Persistent model cache so we don't re-download every job
OLLAMA_CACHE="${HOME}/.ollama_cache"
mkdir -p "$OLLAMA_CACHE"

# ── start Ollama server ─────────────────────────────────────────────────
apptainer run --nv \
    --bind "$OLLAMA_CACHE:/root/.ollama" \
    docker://ollama/ollama serve &

# Wait for server
echo "Waiting for Ollama server..."
for i in $(seq 1 30); do
    if curl -sf "$OLLAMA_SERVER/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    sleep 1
done

# Pull model
echo "Pulling model: $MODEL"
curl -sf "$OLLAMA_SERVER/api/pull" -d "{\"name\": \"$MODEL\"}" > /dev/null

# ── run experiment ───────────────────────────────────────────────────────
ARGS=""
[ -n "$PERSONA" ]  && ARGS="$ARGS --persona $PERSONA"
[ -n "$QUESTION" ] && ARGS="$ARGS --question $QUESTION"

export OLLAMA_MODEL="$MODEL"
export OLLAMA_URL="$OLLAMA_SERVER/api/chat"
export LLM_BACKEND=ollama

python3 experiment.py --runs "$RUNS" $ARGS

echo "=== Experiment complete ==="
