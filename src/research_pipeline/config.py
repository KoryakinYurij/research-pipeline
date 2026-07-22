"""Configuration via environment variables. No external dependencies — os.getenv is sufficient for this prototype."""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # research-pipeline/
TASKS_DIR = BASE_DIR / "tasks"
REPORTS_DIR = BASE_DIR / "reports"

# Google AI Studio
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMMA_MODEL_ID: str = os.getenv("GEMMA_MODEL_ID", "gemma-4-31b-it")

# CLI settings
CLI_TIMEOUT: int = int(os.getenv("CLI_TIMEOUT", "120"))


def ensure_dirs() -> None:
    """Create output directories if they don't exist.

    Called explicitly from dispatcher.main() — NOT at import time,
    to avoid side effects during pytest/ruff runs.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
