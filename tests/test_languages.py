from pathlib import Path
from typing import Any, Dict, Iterable, Set

import pytest
import yaml
from hassil import Intents, recognize
from hassil.expression import Expression, ListReference, RuleReference, Sequence
from hassil.intents import SlotList, TextSlotList
from hassil.util import merge_dict

_DIR = Path(__file__).parent
_BASE_DIR = _DIR.parent
_USER_SENTENCES_DIR = _BASE_DIR / "sentences"
_TEST_SENTENCES_DIR = _BASE_DIR / "tests"

_LANGUAGES = ["en"]


@pytest.fixture(scope="session")
def intent_schemas():
    """Loads the base intents file"""
    with open(_BASE_DIR / "intents.yaml", "r", encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


@pytest.mark.parametrize("language", _LANGUAGES)
def test_language_sentences(language: str):
    """Tests recognition all of the test sentences for a language"""
    intents = load_intents(language)
    tests = load_tests(language)

    slot_lists: Dict[str, SlotList] = {
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
            assert result is not None, f"Recognition failed for '{sentence}'"
            assert (
                result.intent.name == intent["name"]
            ), f"Expected intent {intent['name']}, got {result.intent.name}"
            for slot_name, slot_dict in intent.get("slots", {}).items():
                assert slot_name in result.entities
                assert result.entities[slot_name].value == slot_dict["value"]


@pytest.mark.parametrize("language", _LANGUAGES)
def test_language_intents(language: str, intent_schemas):
    """Ensure all language sentences contain valid slots, lists, rules, etc."""
    intents = load_intents(language)

    # Ensure all intents names are present
    assert intents.intents.keys() == intent_schemas.keys()

    # Add placeholder slots that HA will generate
    intents.slot_lists["area"] = TextSlotList(values=[])
    intents.slot_lists["name"] = TextSlotList(values=[])

    # Lint sentences
    for intent_name, intent in intents.intents.items():
        intent_schema = intent_schemas[intent_name]
        slot_schema = intent_schema["slots"]
        slot_combinations = intent_schema.get("slot_combinations")

        for data in intent.data:
            for sentence in data.sentences:
                found_slots: Set[str] = set()
                for expression in _flatten(sentence):
                    _verify(
                        expression,
                        intents,
                        intent_name,
                        slot_schema,
                        visited_rules=set(),
                        found_slots=found_slots,
                    )

                # Check required slots
                for slot_name, slot_info in slot_schema.items():
                    if slot_info.get("required", False):
                        assert (
                            slot_name in found_slots
                        ), f"Missing required slot: '{slot_name}', intent='{intent_name}', sentence='{sentence.text}'"

                if slot_combinations:
                    # Verify one of the combinations is matched
                    combo_matched = False
                    for combo_slots in slot_combinations.values():
                        if set(combo_slots) == found_slots:
                            combo_matched = True
                            break

                    assert (
                        combo_matched
                    ), f"Slot combination not matched: intent='{intent_name}', slots={found_slots}, sentence='{sentence.text}'"


def _verify(
    expression: Expression,
    intents: Intents,
    intent_name: str,
    slot_schema: Dict[str, Any],
    visited_rules: Set[str],
    found_slots: Set[str],
):
    if isinstance(expression, ListReference):
        list_ref: ListReference = expression

        # Ensure list exists
        assert (
            list_ref.list_name in intents.slot_lists
        ), f"Missing slot list: {{{list_ref.list_name}}}"

        # Ensure slot is part of intent
        assert (
            list_ref.slot_name in slot_schema
        ), f"Unexpected slot '{list_ref.slot_name}' in intent '{intent_name}"

        # Track slots for combination check
        found_slots.add(list_ref.slot_name)
    elif isinstance(expression, RuleReference):
        rule_ref: RuleReference = expression
        assert (
            rule_ref.rule_name in intents.expansion_rules
        ), f"Missing expansion rule: <{rule_ref.rule_name}>"

        # Check for recursive rules (not supported)
        assert (
            rule_ref.rule_name not in visited_rules
        ), f"Recursive rule detected: <{rule_ref.rule_name}>"

        visited_rules.add(rule_ref.rule_name)

        # Verify rule body
        for body_expression in _flatten(intents.expansion_rules[rule_ref.rule_name]):
            _verify(
                body_expression,
                intents,
                intent_name,
                slot_schema,
                visited_rules,
                found_slots,
            )


def _flatten(expression: Expression) -> Iterable[Expression]:
    if isinstance(expression, Sequence):
        seq: Sequence = expression
        for item in seq.items:
            yield from _flatten(item)
    else:
        yield expression


def load_intents(language: str):
    """Load sentences/intents from sentences/ for a language"""
    lang_dir = _USER_SENTENCES_DIR / language
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
    lang_dir = _TEST_SENTENCES_DIR / language
    tests_dict: Dict[str, Any] = {}
    for yaml_path in lang_dir.rglob("*.yaml"):
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(tests_dict, yaml.safe_load(yaml_file))

    assert tests_dict, "No test YAML files loaded"
    return tests_dict
