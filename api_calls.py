"""
api_calls.py

LLM caller for Ollama (local / HPC).
Matches the calling convention from mafiAI's llamacall.py.
"""

import os
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


def call_llm(system_prompt, user_prompt, model=None):
    """Call an LLM via Ollama with the given system and user prompts."""
    model = model or OLLAMA_MODEL
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]


if __name__ == "__main__":
    print("LLM RESPONSE:", call_llm(
        system_prompt="you are just a test, return OK",
        user_prompt="return things are groovy",
    ))
