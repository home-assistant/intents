"""Test language sentences."""
import sys

import pytest
from hassil import recognize
from hassil.intents import TextSlotList

from . import TEST_SENTENCES_DIR


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture(language_tests_yaml):
    """Loads the slot lists for the language."""
    fixtures = language_tests_yaml["_fixtures.yaml"]
    return {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in fixtures["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in fixtures["entities"]
        ),
    }


def do_test_language_sentences_file(
    test_file, language_tests_yaml, slot_lists, language_sentences
):
    """Tests recognition all of the test sentences for a language"""
    for test in language_tests_yaml[test_file]["tests"]:
        intent = test["intent"]
        for sentence in test["sentences"]:
            result = recognize(sentence, language_sentences, slot_lists=slot_lists)
            assert result is not None, f"Recognition failed for '{sentence}'"
            assert (
                result.intent.name == intent["name"]
            ), f"For '{sentence}' expected intent {intent['name']}, got {result.intent.name}"
            for slot_name, slot_dict in intent.get("slots", {}).items():
                if not isinstance(slot_dict, dict):
                    slot_dict = {"value": slot_dict}
                assert (
                    slot_name in result.entities
                ), f"For '{sentence}' did not receive slot '{slot_name}'"
                assert result.entities[slot_name].value == slot_dict["value"]


def gen_test(test_file):
    def test_func(language_tests_yaml, slot_lists, language_sentences):
        do_test_language_sentences_file(
            test_file.name, language_tests_yaml, slot_lists, language_sentences
        )

    test_func.__name__ = f"test_{test_file.stem}"
    setattr(sys.modules[__name__], test_func.__name__, test_func)


def gen_tests():
    lang_dir = TEST_SENTENCES_DIR / "en"

    for test_file in lang_dir.glob("*.yaml"):
        if test_file.name != "_fixtures.yaml":
            gen_test(test_file)


gen_tests()
