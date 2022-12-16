"""Costants."""

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SENTENCE_DIR = ROOT / "sentences"
RESPONSE_DIR = ROOT / "responses"
TESTS_DIR = ROOT / "tests"
INTENTS_FILE = ROOT / "intents.yaml"
LANGUAGES = [p.name for p in SENTENCE_DIR.iterdir() if p.is_dir()]
