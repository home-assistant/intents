"""Test language sentences."""

import pytest

from hassil import recognize
from hassil.intents import TextSlotList


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture(language_tests):
    """Loads the slot lists for the language."""
    return {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in language_tests["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in language_tests["entities"]
        ),
    }


def test_language_sentences(slot_lists, language_intents, language_tests):
    """Tests recognition all of the test sentences for a language"""
    for test in language_tests["tests"]:
        intent = test["intent"]
        for sentence in test["sentences"]:
            result = recognize(sentence, language_intents, slot_lists=slot_lists)
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
