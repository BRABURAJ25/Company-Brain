"""All settings in one place. Change here, nothing else needs to change."""
import os

FALKOR_HOST = os.getenv("FALKOR_HOST", "localhost")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))

# One fixed graph name everywhere (seed.py, brain.py, and the browser UI).
GRAPH_NAME = "company_brain"

# Free local LLM through Ollama (no API key, no cost).
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
