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

_LANGUAGE = "en"


@pytest.fixture
def intents():
    input_dict = {}
    for yaml_path in _USER_SENTENCES_DIR.rglob(f"{_LANGUAGE}.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(input_dict, yaml.safe_load(yaml_file))

    return Intents.from_dict(input_dict)


@pytest.fixture
def tests():
    tests_dict = {}
    for yaml_path in _TEST_SENTENCES_DIR.rglob(f"{_LANGUAGE}.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(tests_dict, yaml.safe_load(yaml_file))

    return tests_dict


def test_language(intents, tests):
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
