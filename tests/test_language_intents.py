"""Test language intents."""
from typing import Any, Dict, Iterable, Set

import pytest
from hassil import Intents
from hassil.expression import Expression, ListReference, RuleReference, Sequence
from hassil.intents import TextSlotList

from . import LANGUAGES


def test_language_intents(language_intents, intent_schemas):
    """Ensure all language sentences contain valid slots, lists, rules, etc."""
    # Ensure all intents names are present
    from pprint import pprint

    pprint(language_intents)
    assert sorted(language_intents.intents) == sorted(intent_schemas)

    # Add placeholder slots that HA will generate
    language_intents.slot_lists["area"] = TextSlotList(values=[])
    language_intents.slot_lists["name"] = TextSlotList(values=[])

    # Lint sentences
    for intent_name, intent in language_intents.intents.items():
        intent_schema = intent_schemas[intent_name]
        slot_schema = intent_schema["slots"]
        slot_combinations = intent_schema.get("slot_combinations")

        for data in intent.data:
            for sentence in data.sentences:
                found_slots: Set[str] = set()
                for expression in _flatten(sentence):
                    _verify(
                        expression,
                        language_intents,
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
