"""Tests."""
from pathlib import Path
from typing import Any, Dict

import yaml
from hassil import Intents
from hassil.util import merge_dict

_DIR = Path(__file__).parent
_BASE_DIR = _DIR.parent
INTENTS_FILE = _BASE_DIR / "intents.yaml"
USER_SENTENCES_DIR = _BASE_DIR / "sentences"
TEST_SENTENCES_DIR = _BASE_DIR / "tests"

LANGUAGES = ["en"]


def load_intents(language: str):
    """Load sentences/intents from sentences/ for a language"""
    lang_dir = USER_SENTENCES_DIR / language
    input_dict: Dict[str, Any] = {}
    for yaml_path in lang_dir.glob("*.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            yaml_dict = yaml.safe_load(yaml_file)
            assert "language" in yaml_dict, f"Missing language: {yaml_path}"
            assert (
                yaml_dict["language"] == language
            ), f"Expected language '{language}', got '{yaml_dict['language']}'"
            merge_dict(input_dict, yaml_dict)

    assert input_dict, "No intent YAML files laoded"
    return Intents.from_dict(input_dict)


def load_tests(language: str):
    """Load test sentences from tests/ for a language"""
    lang_dir = TEST_SENTENCES_DIR / language
    tests_dict: Dict[str, Any] = {}
    for yaml_path in lang_dir.rglob("*.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(tests_dict, yaml.safe_load(yaml_file))

    assert tests_dict, "No test YAML files loaded"
    return tests_dict
