"""Test language intents."""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Any, Iterable

from hassil import Intents
from hassil.expression import (
    Expression,
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
)
from hassil.intents import TextSlotList

from . import SENTENCES_DIR


def test_language_common(
    language: str,
    language_sentences_yaml: dict[str, Any],
) -> None:
    """Test the language common file."""
    common_files = [key for key in language_sentences_yaml if key.startswith("_")]

    assert common_files == [
        "_common.yaml"
    ], "Only _common.yaml is allowed as common file"

    if language == "en":
        return

    content = language_sentences_yaml["_common.yaml"]

    if values := content["lists"].get("color", {}).get("values", []):
        for color in values:
            assert isinstance(
                color, dict
            ), "Color list should use the in-out format to output English color names for Home Assistant to consume. See sentences/nl/_common.yaml for an example."

    assert (
        "intents" not in content
    ), "_common.yaml is a common file and should not contain intents"


def do_test_language_sentences(
    file_name: str,
    intent_schemas: dict[str, Any],
    language_sentences_yaml: dict[str, Any],
    language_sentences_common: Intents,
) -> None:
    """Ensure all language sentences contain valid slots, lists, rules, etc."""
    if file_name not in language_sentences_yaml:
        return

    file_domain, file_intent = Path(file_name).stem.rsplit("_", maxsplit=1)

    parsed_sentences_without_common = Intents.from_dict(
        language_sentences_yaml[file_name]
    )

    # Merge common rules with file specific intents.
    language_sentences = dataclasses.replace(
        language_sentences_common, intents=parsed_sentences_without_common.intents
    )

    # Add placeholder slots that HA will generate
    language_sentences.slot_lists["area"] = TextSlotList(values=[])
    language_sentences.slot_lists["name"] = TextSlotList(values=[])

    # Lint sentences
    for intent_name, intent in language_sentences.intents.items():
        assert (
            file_intent == intent_name
        ), f"File {file_name} should only contain sentences for intent {file_intent}"

        intent_schema = intent_schemas[intent_name]
        slot_schema = intent_schema.get("slots", {})
        slot_combinations = intent_schema.get("slot_combinations")

        for data in intent.data:
            if not data.sentences:
                continue

            expansion_rules = language_sentences.expansion_rules | data.expansion_rules

            if file_domain != "homeassistant":
                # Domain specific files (ie light_HassTurnOn.yaml) should only match
                # sentences for the light domain.
                if intent_schemas[file_intent]["domain"] == file_domain:
                    assert (
                        "domain" not in data.slots
                    ), f"File {file_name} should only have sentences without a domain slot"
                else:
                    assert (data.slots.get("domain") == file_domain) or (
                        data.requires_context.get("domain") == file_domain
                    ), f"File {file_name} should only have sentences with a domain slot or context key set to {file_domain}"

            for sentence in data.sentences:
                found_slots: set[str] = set()
                for expression in _flatten(sentence):
                    _verify(
                        expression,
                        language_sentences,
                        intent_name,
                        slot_schema,
                        visited_rules=set(),
                        found_slots=found_slots,
                        expansion_rules=expansion_rules,
                    )

                # Add inferred slots
                found_slots.update(data.slots)
                if data.requires_context:
                    found_slots.update(data.requires_context)

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
                        if found_slots.issuperset(combo_slots):
                            combo_matched = True
                            break

                    assert (
                        combo_matched
                    ), f"Slot combination not matched: intent='{intent_name}', slots={found_slots}, sentence='{sentence.text}'"


def _verify(
    expression: Expression,
    intents: Intents,
    intent_name: str,
    slot_schema: dict[str, Any],
    visited_rules: set[str],
    found_slots: set[str],
    expansion_rules: dict[str, Sentence],
) -> None:
    if isinstance(expression, ListReference):
        list_ref: ListReference = expression

        # Ensure list exists
        assert (
            list_ref.list_name in intents.slot_lists
        ), f"Missing slot list: {{{list_ref.list_name}}}. Are you missing a 'lists' entry in _common.yaml?"

        # Ensure slot is part of intent
        assert (
            list_ref.slot_name in slot_schema
        ), f"Intent {intent_name} does not support slot '{list_ref.slot_name}'. See intents.yaml for supported slots"

        # Track slots for combination check
        found_slots.add(list_ref.slot_name)
    elif isinstance(expression, RuleReference):
        rule_ref: RuleReference = expression
        assert (
            rule_ref.rule_name in expansion_rules
        ), f"Missing expansion rule: <{rule_ref.rule_name}>. Are you missing an 'expansion_rules' entry in _common.yaml or in the intent data?"

        # Check for recursive rules (not supported)
        assert (
            rule_ref.rule_name not in visited_rules
        ), f"Recursive rule detected: <{rule_ref.rule_name}>"

        # Verify rule body
        for body_expression in _flatten(expansion_rules[rule_ref.rule_name]):
            visited_rules.add(rule_ref.rule_name)
            _verify(
                body_expression,
                intents,
                intent_name,
                slot_schema,
                visited_rules,
                found_slots,
                expansion_rules,
            )
            visited_rules.remove(rule_ref.rule_name)


def _flatten(expression: Expression) -> Iterable[Expression]:
    if isinstance(expression, Sequence):
        seq: Sequence = expression
        for item in seq.items:
            yield from _flatten(item)
    else:
        yield expression


def gen_test(test_file: str) -> None:
    def test_func(
        intent_schemas: dict[str, Any],
        language_sentences_yaml: dict[str, Any],
        language_sentences_common: Intents,
    ) -> None:
        do_test_language_sentences(
            test_file,
            intent_schemas,
            language_sentences_yaml,
            language_sentences_common,
        )

    test_func.__name__ = f"test_{test_file.rsplit('.', 1)[0]}"
    setattr(sys.modules[__name__], test_func.__name__, test_func)


def gen_tests() -> None:
    names = {
        test_file.name
        for test_file in SENTENCES_DIR.glob("*/*.yaml")
        if test_file.name != "_common.yaml"
    }

    for name in names:
        gen_test(name)


gen_tests()
