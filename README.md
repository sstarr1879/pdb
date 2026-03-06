# PDB: Persona-Driven Briefing Experiment

Investigating whether LLMs provide different answers to identical factual questions when the requester's identity changes. Framed as an intelligence briefing scenario where the same facts should be delivered regardless of who asks.

## Research Question

Do LLMs distort, omit, or paternalistically filter factual intelligence content based on who is asking?

## Experiment Design

**8 personas** spanning authority, expertise, and intent:

| Persona | Role |
|---|---|
| Senior Analyst | 20-year IC veteran preparing a classified briefing |
| Junior Analyst | Entry-level analyst writing their first assessment |
| Policy Maker | Cabinet-level official needing actionable intelligence |
| Journalist | Investigative reporter covering national security |
| Graduate Student | International PhD student researching nonproliferation |
| Concerned Parent | No expertise, worried after a news headline |
| Military Commander | Operational commander planning deployment |
| Arms Dealer | Adversarial test — fictional black-market figure |

**4 question domains:**
- Nuclear proliferation (Iran enrichment program)
- Biological threats (China dual-use research)
- Cyber threats (Russian APT groups)
- Economic sanctions (North Korea evasion)

**Per run:** 8 personas x 4 questions x 3 runs = 96 LLM calls

## Metrics

Each response is scored on:
- **Word count** — does the model give more or less detail?
- **Hedge count** — uncertainty language, caveats, disclaimers
- **Specificity hits** — concrete facts, numbers, named entities
- **Refusal detection** — outright refusals to answer
- **Hedge/specificity density** — normalized per 1000 words

## Project Structure

```
pdb/
├── experiment.py          # Main experiment loop
├── personas.py            # Persona definitions and system prompts
├── questions.py           # Question bank by domain
├── metrics.py             # Response analysis (hedging, refusals, specificity)
├── api_calls.py           # Ollama LLM caller
├── aggregate_results.py   # Collects runs into CSV + summary tables
├── experiment.sbatch      # SLURM job script for HPC (A100)
├── batch_experiments.sh   # Submit jobs across multiple models
└── runs/                  # Output directory (one subdir per experiment)
```

## Running on HPC (Pegasus)

### Interactive test

```bash
salloc --partition=gpu --gres=gpu:a100:1 --mem=64G --time=00:30:00
ssh <gpu_node>
module load apptainer
mkdir -p ~/.ollama_cache
apptainer run --nv --bind ~/.ollama_cache:/root/.ollama docker://ollama/ollama serve &
# wait a few seconds
export OLLAMA_MODEL=llama3.1:70b
python3 experiment.py --persona senior_analyst --question nuclear --runs 1
```

### Batch submission

```bash
# Full experiment on A100 with 70b
sbatch --partition=gpu --gres=gpu:a100:1 --mem=64G experiment.sbatch

# 8b model on smaller GPU
sbatch --partition=debug-gpu --gres=gpu:1 --mem=32G --export=ALL,OLLAMA_MODEL=llama3.1:8b experiment.sbatch
```

### Monitor and aggregate

```bash
squeue -u $USER                    # check job status
tail -f slurm-<jobid>.out         # watch progress
python3 aggregate_results.py       # generate CSV + summary tables
```

## Output

Each run creates a timestamped directory under `runs/` containing:
- `config.json` — experiment parameters
- `results.jsonl` — one JSON record per LLM call (response, metrics, metadata)

`aggregate_results.py` produces:
- `experiment_results.csv` — all metrics in tabular form
- `experiment_results.json` — full results including response text
- Pivot tables by persona and question domain
- Refusal matrix (persona x question)
