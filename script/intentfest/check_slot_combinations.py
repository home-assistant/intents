"""Check support for intent slot combinations."""

from __future__ import annotations

import argparse
import itertools
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union

import yaml
from hassil.expression import (
    Expression,
    ListReference,
    RuleReference,
    Sequence,
    SequenceType,
)
from hassil.intents import IntentData, Intents

from .const import INTENTS_FILE, LANGUAGES, SENTENCE_DIR
from .util import get_base_arg_parser

CONTEXT_AREA_SLOT = "__context_area__"


class SupportLevel(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    EXTRA = "extra"
    NONE = "none"


@dataclass
class LanguageIntentSupport:
    level: str
    matching: List[List[str]] = field(default_factory=list)
    missing: List[List[str]] = field(default_factory=list)
    extra: List[List[str]] = field(default_factory=list)


@dataclass
class IntentSupport:
    support_by_language: Dict[str, LanguageIntentSupport] = field(default_factory=dict)


@dataclass
class Node:
    children: "List[Node]" = field(default_factory=list)
    slot_names: Set[str] = field(default_factory=set)


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument("--output", help="Path to write YAML report (default: stdout)")
    parser.add_argument(
        "--language", type=str, choices=LANGUAGES, help="The language to check."
    )
    parser.add_argument("--intent", help="Name of intent to check.")
    parser.add_argument(
        "--skip-full",
        action="store_true",
        help="Don't report language intents with full support.",
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

    support_by_intent: Dict[str, IntentSupport] = {}

    for intent_name, intent_info in intents.items():
        if not intent_info.get("supported", False):
            # Skip intents that aren't supported in HA core
            continue

        if intent_name in ("HassGetState",):
            # Ignore HassGetState for now
            continue

        if args.intent and (intent_name != args.intent):
            continue

        slot_combinations = intent_info.get("slot_combinations")
        if not slot_combinations:
            # CI should fail
            raise ValueError(f"Missing slot_combinations for intent: {intent_name}")

        intent_support = IntentSupport()
        support_by_intent[intent_name] = intent_support

        for language in languages:
            lang_support = LanguageIntentSupport(level=SupportLevel.NONE.value)
            intent_support.support_by_language[language] = lang_support

            lang_intents = Intents.from_files((SENTENCE_DIR / language).glob("*.yaml"))
            intent = lang_intents.intents.get(intent_name)
            if intent is None:
                # Language does not have intent at all
                continue

            expected_slot_combos: Set[Tuple[str, ...]] = set()
            for combo in slot_combinations:
                combo_slots = combo["slots"]
                if isinstance(combo_slots, str):
                    combo_slots = [combo_slots]

                if combo.get("context_area", False):
                    combo_slots.append(CONTEXT_AREA_SLOT)

                expected_slot_combos.update(
                    tuple(sorted(combo_slots)) for combo in slot_combinations
                )

            actual_slot_combos: Set[Tuple[str, ...]] = set()
            combo_sentences = defaultdict(set)

            for data in intent.data:
                auto_slots = set()
                if data.slots:
                    # Inferred slots
                    auto_slots.update(data.slots.keys())

                if data.requires_context.get("area", {}).get("slot"):
                    # Context area
                    auto_slots.add(CONTEXT_AREA_SLOT)

                for sentence in data.sentences:
                    sentence_combos: Set[Tuple[str, ...]] = set()
                    for combo in _get_slots(sentence, data, lang_intents):
                        if combo is None:
                            combo_tuple = tuple(auto_slots)
                        else:
                            # Must be sorted to match expected
                            combo_tuple = tuple(
                                sorted(itertools.chain(auto_slots, _flatten(combo)))
                            )

                        sentence_combos.add(combo_tuple)
                        combo_sentences[combo_tuple].add(sentence.text)

                    actual_slot_combos.update(sentence_combos)

            # lang_support.matching = [
            #     {
            #         "slots": list(combo),
            #         "sentences": sorted(sentences),
            #     }
            #     for combo, sentences in sorted(combo_sentences.items())
            #     if combo in expected_slot_combos
            # ]

            missing_combos = expected_slot_combos - actual_slot_combos
            if missing_combos:
                lang_support.level = SupportLevel.PARTIAL.value
                lang_support.missing = [list(combo) for combo in sorted(missing_combos)]
                continue

            extra_combos = actual_slot_combos - expected_slot_combos
            if extra_combos:
                lang_support.level = SupportLevel.EXTRA.value
                lang_support.extra = [
                    {
                        "slots": list(combo),
                        "sentences": sorted(sentences),
                    }
                    for combo, sentences in sorted(combo_sentences.items())
                    if combo in extra_combos
                ]
                continue

            lang_support.level = SupportLevel.FULL.value
            if args.skip_full:
                # Exclude from report
                intent_support.support_by_language.pop(language)

    if args.output:
        yaml_path = Path(args.output)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_file = open(yaml_path, "w", encoding="utf-8")
    else:
        yaml_file = sys.stdout

    yaml.safe_dump(
        {
            intent_name: asdict(intent_support)
            for intent_name, intent_support in support_by_intent.items()
            if intent_support.support_by_language
        },
        yaml_file,
    )


# -----------------------------------------------------------------------------


def _get_slots(
    e: Expression, data: IntentData, intents: Intents
) -> Iterable[Union[str, None]]:
    if isinstance(e, Sequence):
        seq: Sequence = e
        if seq.type == SequenceType.GROUP:
            seq_slots = map(partial(_get_slots, data=data, intents=intents), seq.items)
            yield from itertools.product(*seq_slots)
        elif seq.type == SequenceType.ALTERNATIVE:
            for item in seq.items:
                yield from _get_slots(item, data, intents)
        else:
            raise ValueError(f"Unexpected sequence type: {seq.type}")
    elif isinstance(e, ListReference):
        list_ref: ListReference = e
        yield list_ref.slot_name
    elif isinstance(e, RuleReference):
        rule_ref: RuleReference = e
        rule_body = data.expansion_rules.get(rule_ref.rule_name)
        if rule_body is None:
            rule_body = intents.expansion_rules[rule_ref.rule_name]

        if rule_body is None:
            raise ValueError(f"Missing body for expansion rule: {rule_ref.rule_name}")

        yield from _get_slots(rule_body, data, intents)
    else:
        yield None


def _flatten(items: Iterable[Any]) -> Iterable[str]:
    for item in items:
        if item is None:
            continue

        if isinstance(item, str):
            yield item
        else:
            yield from _flatten(item)
