"""Test language sentences."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hassil import Intents, recognize
from hassil.intents import SlotList, TextSlotList

from . import TESTS_DIR, load_test


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture(language: str) -> dict[str, SlotList]:
    """Loads the slot lists for the language."""
    fixtures = load_test(language, "_fixtures")
    return {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in fixtures["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in fixtures["entities"]
        ),
    }


def do_test_language_sentences_file(
    language: str,
    test_file: str,
    slot_lists: dict[str, SlotList],
    language_sentences: Intents,
) -> None:
    """Tests recognition all of the test sentences for a language"""
    _testing_domain, testing_intent = test_file.split("_", 1)

    seen_sentences = set()

    for test in load_test(language, test_file)["tests"]:
        intent = test["intent"]
        assert (
            intent["name"] == testing_intent
        ), f"File {test_file} should only test for intent {testing_intent}"

        for sentence in test["sentences"]:
            assert (
                sentence not in seen_sentences
            ), f"Duplicate sentence found: {sentence}"
            seen_sentences.add(sentence)

            result = recognize(sentence, language_sentences, slot_lists=slot_lists)
            assert result is not None, f"Recognition failed for '{sentence}'"
            assert (
                result.intent.name == intent["name"]
            ), f"For '{sentence}' expected intent {intent['name']}, got {result.intent.name}"
            for slot_name, slot_dict in intent.get("slots", {}).items():
                if not isinstance(slot_dict, dict):
                    slot_dict = {"value": slot_dict}
                assert (
                    slot_name
                    in
                    # wrap it in a list to get more readable pytest assertion
                    list(result.entities)
                ), f"For '{sentence}' did not receive slot '{slot_name}'"
                assert result.entities[slot_name].value == slot_dict["value"]


def gen_test(test_file: Path) -> None:
    def test_func(
        language: str,
        slot_lists: dict[str, SlotList],
        language_sentences: Intents,
    ) -> None:
        do_test_language_sentences_file(
            language, test_file.stem, slot_lists, language_sentences
        )

    test_func.__name__ = f"test_{test_file.stem}"
    setattr(sys.modules[__name__], test_func.__name__, test_func)


def gen_tests() -> None:
    lang_dir = TESTS_DIR / "en"

    for test_file in lang_dir.glob("*.yaml"):
        if test_file.name != "_fixtures.yaml":
            gen_test(test_file)


gen_tests()
