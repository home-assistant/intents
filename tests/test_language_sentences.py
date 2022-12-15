"""Test language sentences."""

from typing import Dict

from hassil import recognize
from hassil.intents import SlotList, TextSlotList


def test_language_sentences(language_intents, language_tests):
    """Tests recognition all of the test sentences for a language"""
    slot_lists: Dict[str, SlotList] = {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in language_tests["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in language_tests["entities"]
        ),
    }

    for test in language_tests["tests"]:
        intent = test["intent"]
        for sentence in test["sentences"]:
            result = recognize(sentence, language_intents, slot_lists=slot_lists)
            assert result is not None, f"Recognition failed for '{sentence}'"
            assert (
                result.intent.name == intent["name"]
            ), f"Expected intent {intent['name']}, got {result.intent.name}"
            for slot_name, slot_dict in intent.get("slots", {}).items():
                assert slot_name in result.entities
                assert result.entities[slot_name].value == slot_dict["value"]
