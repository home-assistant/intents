"""Test language sentences."""

from __future__ import annotations

import sys
from contextlib import AbstractContextManager, nullcontext
from typing import Any, List

import pytest
from hassil import Intents, recognize_best
from hassil.intents import SlotList
from hassil.util import normalize_whitespace
from jinja2 import BaseLoader, Environment
from yaml import safe_load

from shared import (
    AreaEntry,
    State,
    Timer,
    get_areas,
    get_matched_states,
    get_matched_timers,
    get_slot_lists,
    get_states,
    get_timers,
    render_response,
)

from . import TESTS_DIR, get_test_path, load_test


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture(language: str) -> dict[str, SlotList]:
    """Loads the slot lists for the language."""
    fixtures = load_test(language, "_fixtures")
    return get_slot_lists(fixtures)


@pytest.fixture(name="states", scope="session")
def states_fixture(language: str) -> List[State]:
    """Loads test entity states for the language."""
    fixtures = load_test(language, "_fixtures")
    return get_states(fixtures)


@pytest.fixture(name="areas", scope="session")
def areas_fixture(language: str) -> List[AreaEntry]:
    """Loads test areas for the language."""
    fixtures = load_test(language, "_fixtures")
    return get_areas(fixtures)


@pytest.fixture(name="timers", scope="session")
def timers_fixture(language: str) -> List[Timer]:
    """Loads test timers for the language."""
    fixtures = load_test(language, "_fixtures")
    return get_timers(fixtures)


def do_test_language_sentences_file(
    language: str,
    test_file: str,
    *,
    intent_schemas: dict[str, Any],
    slot_lists: dict[str, SlotList],
    states: List[State],
    areas: List[AreaEntry],
    timers: List[Timer],
    language_sentences: Intents,
    language_responses: dict[str, Any],
) -> None:
    """Tests recognition all of the test sentences for a language"""
    if not get_test_path(language, test_file).exists():
        return

    # Load sentences that are expected to fail.
    #
    # These will be run in a pytest.raises(Exception) context so they must be
    # removed when fixed.
    failing_sentences: set[str] = set()
    test_failures_path = TESTS_DIR / language / "_test_failures.yaml"
    if test_failures_path.exists():
        with open(test_failures_path, "r", encoding="utf-8") as test_failures_file:
            test_failures_dict = safe_load(test_failures_file)
            failing_sentences.update(test_failures_dict.get("sentences", []))

    testing_domain, testing_intent = test_file.rsplit("_", maxsplit=1)

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
                assert ("domain" not in intent.get("slots", {})) and (
                    "domain" not in intent.get("context", {})
                ), f"File {test_file}: tests should not have a domain slot"
            else:
                assert (intent.get("slots", {}).get("domain") == testing_domain) or (
                    intent.get("context", {}).get("domain") == testing_domain
                ), f"File {test_file}: tests should have domain slot set to {testing_domain}"

        intent_context = intent.get("context", {})
        expected_response_texts = test.get("response")
        if expected_response_texts:
            if isinstance(expected_response_texts, str):
                expected_response_texts = {expected_response_texts.strip()}
            else:
                expected_response_texts = set(
                    t.strip() for t in expected_response_texts
                )

        for sentence in test["sentences"]:
            assert (
                sentence not in seen_sentences
            ), f"Duplicate sentence found: {sentence}"
            seen_sentences.add(sentence)

            if sentence in failing_sentences:
                # Expected to fail
                sentence_context: AbstractContextManager = pytest.raises(Exception)
                expected_to_fail = True
            else:
                # Expected to pass
                sentence_context = nullcontext()
                expected_to_fail = False

            with sentence_context:
                result = recognize_best(
                    sentence,
                    language_sentences,
                    slot_lists=slot_lists,
                    intent_context=intent_context,
                    best_slot_name="name",
                )
                assert result is not None, f"Recognition failed for '{sentence}'"
                assert (
                    result.intent.name == intent["name"]
                ), f"For '{sentence}' expected intent {intent['name']}, got {result.intent.name}"

                matched_slots = {
                    slot.name: slot.value for slot in result.entities.values()
                }
                actual_slots = intent.get("slots") or {}

                # Check for all match slots
                for match_name, match_value in matched_slots.items():
                    actual_value = actual_slots.get(match_name)
                    assert (
                        actual_value is not None
                    ), f"Missing slot {match_name} for: {sentence} (value={match_value})"

                    if isinstance(actual_value, list):
                        actual_value_set = set(actual_value)
                        if isinstance(match_value, list):
                            # Both are lists
                            assert actual_value_set.issubset(
                                match_value
                            ), f"Slots do not match for: {sentence}"
                        else:
                            # Actual is a list, match is a single value
                            assert (
                                match_value in actual_value_set
                            ), f"Slot {match_name} must be one of {match_value} for: {sentence}"
                    else:
                        if isinstance(match_value, list):
                            # Match is a list, actual is a single value
                            assert (
                                actual_value in match_value
                            ), f"Slot {match_name} must be one of {match_value} for: {sentence}"
                        else:
                            # Both are single values
                            assert (
                                actual_value == match_value
                            ), f"Expected {match_value}, got {actual_value} for slot {match_name} for: {sentence}"

                # Verify no extra slots
                for actual_name in actual_slots:
                    assert (
                        actual_name in matched_slots
                    ), f"Slot {actual_name} was not expected for: {sentence}"

                # Verify context if it's used in the test.
                #
                # This result "context" is acquired during matching; a hassil slot
                # list item may have a "context" which is added to the result
                # context if that item is matched.
                actual_context = intent.get("context", {})
                if actual_context:
                    matched_context = result.context
                    assert (
                        matched_context == actual_context
                    ), f"Expected context {actual_context}, got {matched_context} for intent {result.intent.name}: {sentence}"

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

                    matched, unmatched = get_matched_states(states, areas, result)
                    actual_response_text = render_response(
                        response_template_str,
                        result,
                        matched,
                        unmatched,
                        env=template_env,
                        timers=get_matched_timers(timers, result),
                    )
                    actual_response_text = normalize_whitespace(
                        actual_response_text
                    ).strip()
                    assert (
                        actual_response_text in expected_response_texts
                    ), f"Incorrect response for: {sentence}"

                if expected_to_fail:
                    pytest.fail(f"Expected sentence to fail but it didn't: {sentence}")


def gen_test(test_file_stem: str) -> None:
    def test_func(
        language: str,
        *,
        intent_schemas: dict[str, Any],
        slot_lists: dict[str, SlotList],
        states: List[State],
        areas: List[AreaEntry],
        timers: List[Timer],
        language_sentences: Intents,
        language_responses: dict[str, Any],
    ) -> None:
        do_test_language_sentences_file(
            language,
            test_file_stem,
            intent_schemas=intent_schemas,
            slot_lists=slot_lists,
            states=states,
            areas=areas,
            timers=timers,
            language_sentences=language_sentences,
            language_responses=language_responses,
        )

    test_func.__name__ = f"test_{test_file_stem}"
    setattr(sys.modules[__name__], test_func.__name__, test_func)


def gen_tests() -> None:
    names = {
        test_file.stem
        for test_file in TESTS_DIR.glob("*/*.yaml")
        if test_file.name not in ("_fixtures.yaml", "_test_failures.yaml")
    }

    for name in sorted(names):
        gen_test(name)


gen_tests()
