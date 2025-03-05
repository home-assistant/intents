"""Check support for intent slot combinations."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Set

import yaml
from hassil.expression import (
    Expression,
    ListReference,
    RuleReference,
    Sequence,
    SequenceType,
)
from hassil.intents import IntentData, Intents

from .const import (
    INTENTS_FILE,
    LANGUAGES,
    LANGUAGES_FILE,
    RESPONSE_DIR,
    ROOT,
    SENTENCE_DIR,
    TESTS_DIR,
)
from .util import get_base_arg_parser


@dataclass
class Node:
    children: "List[Node]" = field(default_factory=list)
    slot_names: Set[str] = field(default_factory=set)
    is_optional: bool = False


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language", type=str, choices=LANGUAGES, help="The language to check."
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    with open(INTENTS_FILE, "r", encoding="utf-8") as intents_file:
        intents = yaml.safe_load(intents_file)

    if args.language is None:
        languages = LANGUAGES
    else:
        languages = [args.language]

    for language in languages:
        print("Language:", language)
        lang_intents = Intents.from_files((SENTENCE_DIR / language).glob("*.yaml"))

        for intent_name, intent_info in intents.items():
            if not intent_info.get("supported", False):
                continue

            intent = lang_intents.intents.get(intent_name)
            if intent is None:
                continue

            slot_combinations = intent_info.get("slot_combinations")
            if not slot_combinations:
                continue

            expected_slot_combos = set(
                tuple(sorted(combo)) for combo in slot_combinations.values()
            )
            actual_slot_combos = set()
            combo_sentences = defaultdict(list)

            print("Intent:", intent_name)

            for data in intent.data:
                auto_slots = set()
                if data.slots:
                    # Inferred slots
                    auto_slots.update(data.slots.keys())

                if data.requires_context.get("area", {}).get("slot"):
                    # Context area
                    auto_slots.add("area")

                for sentence in data.sentences:
                    root = Node()
                    # print(sentence.text)
                    _get_slots(sentence, data, lang_intents, root)
                    for combo in _get_slot_combos(root, auto_slots):
                        actual_slot_combos.add(combo)
                        combo_sentences[combo].append(sentence)

            missing_combos = expected_slot_combos - actual_slot_combos
            if missing_combos:
                print("Missing:", missing_combos)

            extra_combos = actual_slot_combos - expected_slot_combos
            for combo in extra_combos:
                print("Extra:", combo)
                for sentence in combo_sentences[combo]:
                    print("  ", sentence.text)

                print("")

            print("")

            # TODO
            break


def _get_slots(
    e: Expression,
    data: IntentData,
    intents: Intents,
    node: Node,
    # in_optional: bool = False,
):
    if isinstance(e, Sequence):
        seq: Sequence = e
        if seq.type == SequenceType.GROUP:
            for item in seq.items:
                _get_slots(item, data, intents, node)
        elif seq.type == SequenceType.ALTERNATIVE:
            for item in seq.items:
                item_node = Node(is_optional=seq.is_optional)
                node.children.append(item_node)
                _get_slots(item, data, intents, item_node)
    elif isinstance(e, ListReference):
        list_ref: ListReference = e
        node.slot_names.add(list_ref.slot_name)
    elif isinstance(e, RuleReference):
        rule_ref: RuleReference = e
        rule_body = data.expansion_rules.get(rule_ref.rule_name)
        if rule_body is None:
            rule_body = intents.expansion_rules[rule_ref.rule_name]

        _get_slots(rule_body, data, intents, node)


def _get_slot_combos(node: Node, slots):
    slot_combos = set()
    for combo in _dfs(node, set(slots)):
        if combo not in slot_combos:
            yield combo
            slot_combos.add(combo)


def _dfs(node: Node, slots):
    if (not node.children) and slots:
        yield tuple(sorted(slots))

    slots.update(node.slot_names)

    for child in node.children:
        yield from _dfs(child, set(slots))
