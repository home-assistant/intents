"""Tests."""

from pathlib import Path
from typing import Any, Dict

import yaml

_DIR = Path(__file__).parent
BASE_DIR = _DIR.parent
INTENTS_FILE = BASE_DIR / "intents.yaml"
SENTENCES_DIR = BASE_DIR / "sentences"
LISTS_DIR = BASE_DIR / "lists"
RULES_DIR = BASE_DIR / "rules"
TESTS_DIR = BASE_DIR / "tests"
RESPONSES_DIR = BASE_DIR / "responses"

LANGUAGES = sorted(p.name for p in SENTENCES_DIR.iterdir() if p.is_dir())


def load_sentences(language: str) -> dict[str, Any]:
    """Load sentences from sentences/ for a language"""
    lang_dir = SENTENCES_DIR / language
    files: Dict[str, Any] = {}

    for yaml_path in sorted(lang_dir.glob("*.yaml")):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            yaml_dict = yaml.safe_load(yaml_file)
            assert "language" in yaml_dict, f"Missing language: {yaml_path}"
            assert (
                yaml_dict["language"] == language
            ), f"Expected language '{language}', got '{yaml_dict['language']}'"
            files[yaml_path.name] = yaml_dict

    return files


def get_test_path(language: str, test_name: str) -> Path:
    """Get path to test YAML file."""
    return TESTS_DIR / language / f"{test_name}.yaml"


def load_test(language: str, test_name: str) -> dict[str, Any]:
    """Load test sentences from tests/ for a language"""
    return yaml.safe_load(get_test_path(language, test_name).read_text())
