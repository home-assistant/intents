"""Test language sentences."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from hassil import Intents, recognize
from hassil.intents import SlotList, TextSlotList
from hassil.util import normalize_whitespace
from jinja2 import BaseLoader, Environment

from . import TESTS_DIR, load_test


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture(language: str) -> dict[str, SlotList]:
    """Loads the slot lists for the language."""
    fixtures = load_test(language, "_fixtures")
    return {
        "area": TextSlotList.from_tuples(
            (area["name"], area["name"]) for area in fixtures["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["name"], _entity_context(entity))
            for entity in fixtures["entities"]
        ),
    }


def _entity_context(entity: dict[str, Any]) -> dict[str, Any]:
    """Extract matching context from test fixture entity."""
    entity_id = entity["id"]
    domain = entity_id.split(".", maxsplit=1)[0]
    return {"domain": domain}


def do_test_language_sentences_file(
    language: str,
    test_file: str,
    intent_schemas: dict[str, Any],
    slot_lists: dict[str, SlotList],
    language_sentences: Intents,
    language_responses: dict[str, Any],
) -> None:
    """Tests recognition all of the test sentences for a language"""
    testing_domain, testing_intent = test_file.split("_", 1)

    seen_sentences = set()
    template_env = Environment(loader=BaseLoader())

    for test in load_test(language, test_file)["tests"]:
        intent = test["intent"]
        assert (
            intent["name"] == testing_intent
        ), f"File {test_file}: Unexpected intent {intent['name']}. Only test for intent {testing_intent}"

        if not test["sentences"]:
            continue

        if testing_domain != "homeassistant":
            # Domain specific files (ie light_HassTurnOn.yaml) should only test
            # sentences for the light domain.
            if intent_schemas[testing_intent]["domain"] == testing_domain:
                assert "domain" not in intent.get(
                    "slots", {}
                ), f"File {test_file}: tests should not have a domain slot"
            else:
                assert (
                    intent.get("slots", {}).get("domain") == testing_domain
                ), f"File {test_file}: tests should have domain slot set to {testing_domain}"

        intent_context = intent.get("context", {})
        expected_response_texts = test.get("response")
        if expected_response_texts:
            if isinstance(expected_response_texts, str):
                expected_response_texts = {expected_response_texts}
            else:
                expected_response_texts = set(expected_response_texts)

        for sentence in test["sentences"]:
            assert (
                sentence not in seen_sentences
            ), f"Duplicate sentence found: {sentence}"
            seen_sentences.add(sentence)

            result = recognize(
                sentence,
                language_sentences,
                slot_lists=slot_lists,
                intent_context=intent_context,
            )
            assert result is not None, f"Recognition failed for '{sentence}'"
            assert (
                result.intent.name == intent["name"]
            ), f"For '{sentence}' expected intent {intent['name']}, got {result.intent.name}"

            matched_slots = {slot.name: slot.value for slot in result.entities.values()}
            actual_slots = intent.get("slots", {})

            # Check for all match slots
            for match_name, match_value in matched_slots.items():
                actual_value = actual_slots.get(match_name)
                assert (
                    actual_value is not None
                ), f"Missing slot {match_name} for: {sentence} (value={match_value})"

                if not isinstance(match_value, list):
                    # Only one acceptable value
                    assert (
                        actual_value == match_value
                    ), f"Expected {match_value}, got {actual_value} for slot {match_name} for: {sentence}"
                    continue

                # One of multiple possibilities
                if isinstance(actual_value, list):
                    actual_value_set = set(actual_value)
                    assert actual_value_set.issubset(
                        match_value
                    ), "Slots do not match for: {sentence}"
                else:
                    assert (
                        actual_value in match_value
                    ), f"Slot {match_name} must be one of {match_value} for: {sentence}"

            # Verify no extra slots
            for actual_name in actual_slots:
                assert (
                    actual_name in matched_slots
                ), f"Slot {actual_name} was not expected for: {sentence}"

            # Verify response
            if expected_response_texts:
                actual_response_key = result.response
                assert actual_response_key, f"Expected a response for: {sentence}"

                response_template_str = language_responses.get(
                    result.intent.name, {}
                ).get(actual_response_key)
                assert (
                    response_template_str
                ), f"No response template for intent {result.intent.name} named {actual_response_key}: {sentence}"

                response_template = template_env.from_string(response_template_str)
                actual_response_text = response_template.render(
                    {
                        "slots": {
                            entity_name: entity_value.text or entity_value.value
                            for entity_name, entity_value in result.entities.items()
                        }
                    }
                )
                actual_response_text = normalize_whitespace(
                    actual_response_text
                ).strip()
                assert (
                    actual_response_text in expected_response_texts
                ), f"Incorrect response for: {sentence}"


def gen_test(test_file: Path) -> None:
    def test_func(
        language: str,
        intent_schemas: dict[str, Any],
        slot_lists: dict[str, SlotList],
        language_sentences: Intents,
        language_responses: dict[str, Any],
    ) -> None:
        do_test_language_sentences_file(
            language,
            test_file.stem,
            intent_schemas,
            slot_lists,
            language_sentences,
            language_responses,
        )

    test_func.__name__ = f"test_{test_file.stem}"
    setattr(sys.modules[__name__], test_func.__name__, test_func)


def gen_tests() -> None:
    lang_dir = TESTS_DIR / "en"

    for test_file in lang_dir.glob("*.yaml"):
        if test_file.name != "_fixtures.yaml":
            gen_test(test_file)


gen_tests()
