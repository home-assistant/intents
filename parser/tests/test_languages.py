from pathlib import Path

import pytest
import yaml

from hassil import Intents, recognize
from hassil.intents import TextSlotList
from hassil.util import merge_dict

_DIR = Path(__file__).parent
_BASE_DIR = _DIR.parent.parent
_USER_SENTENCES_DIR = _BASE_DIR / "sentences"
_TEST_SENTENCES_DIR = _DIR / "sentences"

_LANGUAGES = ["en"]


@pytest.mark.parametrize("language", _LANGUAGES)
def test_language(language: str):
    """Tests all of the sentences for a language"""
    intents = load_intents(language)
    tests = load_tests(language)

    slot_lists = {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in tests["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in tests["entities"]
        ),
    }

    for test in tests["tests"]:
        intent = test["intent"]
        for sentence in test["sentences"]:
            result = recognize(sentence, intents, slot_lists=slot_lists)
            assert result is not None, sentence
            assert result.intent.name == intent["name"]
            for slot_name, slot_dict in intent.get("slots", {}).items():
                assert slot_name in result.entities
                assert result.entities[slot_name].value == slot_dict["value"]


def load_intents(language: str):
    """Load sentences/intents from sentences/ for a language"""
    input_dict = {}
    for yaml_path in _USER_SENTENCES_DIR.rglob(f"{language}.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(input_dict, yaml.safe_load(yaml_file))

    return Intents.from_dict(input_dict)


def load_tests(language: str):
    """Load test sentences from tests/sentences for a language"""
    tests_dict = {}
    for yaml_path in _TEST_SENTENCES_DIR.rglob(f"{language}.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(tests_dict, yaml.safe_load(yaml_file))

    return tests_dict
