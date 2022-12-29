"""Tests."""
from pathlib import Path
from typing import Any, Dict

import yaml

_DIR = Path(__file__).parent
_BASE_DIR = _DIR.parent
INTENTS_FILE = _BASE_DIR / "intents.yaml"
SENTENCES_DIR = _BASE_DIR / "sentences"
TESTS_DIR = _BASE_DIR / "tests"

LANGUAGES = sorted(p.name for p in SENTENCES_DIR.iterdir() if p.is_dir())


def load_sentences(language: str) -> dict[str, Any]:
    """Load sentences from sentences/ for a language"""
    lang_dir = SENTENCES_DIR / language
    files: Dict[str, Any] = {}

    for yaml_path in lang_dir.glob("*.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            yaml_dict = yaml.safe_load(yaml_file)
            assert "language" in yaml_dict, f"Missing language: {yaml_path}"
            assert (
                yaml_dict["language"] == language
            ), f"Expected language '{language}', got '{yaml_dict['language']}'"
            files[yaml_path.name] = yaml_dict

    return files


def load_test(language: str, test_name: str) -> dict[str, Any]:
    """Load test sentences from tests/ for a language"""
    return yaml.safe_load((TESTS_DIR / language / f"{test_name}.yaml").read_text())
