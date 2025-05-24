"""Check support for intent slot combinations."""

from __future__ import annotations

import argparse
import itertools
import logging
import sys
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Set, TextIO, Tuple, Union

import yaml
from hassil import (
    Alternative,
    Expression,
    Group,
    IntentData,
    Intents,
    ListReference,
    Permutation,
    RuleReference,
    Sequence,
)

from .const import INTENTS_FILE, LANGUAGES, SENTENCE_DIR
from .util import get_base_arg_parser

_LOGGER = logging.getLogger(__name__)

CONTEXT_AREA_SLOT = "__context_area__"


class SupportLevel(str, Enum):
    """Level of support for an intent for a given language."""

    FULL = "full"
    """All slot combinations are covered, with no extras."""

    PARTIAL = "partial"
    """Some slot combinations are covered, with no extras."""

    EXTRA = "extra"
    """More slot combinations are covered than are supported by the intent."""

    NONE = "none"
    """No support."""


@dataclass
class LanguageIntentSupport:
    """Intent support details for a language."""

    intent_name: str
    level: str
    # matching: List[List[str]] = field(default_factory=list)
    missing: List[List[str]] = field(default_factory=list)
    extra: List[List[str]] = field(default_factory=list)


@dataclass
class IntentSupport:
    """Support for an intent."""

    support_by_language: Dict[str, LanguageIntentSupport] = field(default_factory=dict)


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
    """Run function."""
    args = get_arguments()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with open(INTENTS_FILE, "r", encoding="utf-8") as intents_file:
        intents = yaml.safe_load(intents_file)

    if args.language is None:
        languages = LANGUAGES
    else:
        languages = [args.language]

    support_by_intent: Dict[str, IntentSupport] = defaultdict(IntentSupport)

    with ProcessPoolExecutor() as executor:
        for language, lang_supports in executor.map(
            partial(_get_support, intents=intents, args=args), languages
        ):
            for lang_support in lang_supports:
                if args.skip_full and (lang_support.level == SupportLevel.FULL.value):
                    # Exclude from report
                    continue

                support_by_intent[lang_support.intent_name].support_by_language[
                    language
                ] = lang_support

    yaml_file: TextIO = sys.stdout

    if args.output:
        yaml_path = Path(args.output)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_file = open(yaml_path, "w", encoding="utf-8")

    yaml.safe_dump(
        {
            intent_name: asdict(intent_support)
            for intent_name, intent_support in support_by_intent.items()
            if intent_support.support_by_language
        },
        yaml_file,
    )

    return 0


def _get_support(language: str, intents: Dict[str, Any], args: argparse.Namespace):
    lang_intents = Intents.from_files((SENTENCE_DIR / language).glob("*.yaml"))
    lang_supports: List[LanguageIntentSupport] = []
    rule_slot_cache: Dict[Tuple[str, bool], Any] = {}

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
            _LOGGER.warning("Missing slot_combinations for intent: %s", intent_name)
            continue

        _LOGGER.debug("Processing %s for %s", language, intent_name)

        lang_support = LanguageIntentSupport(
            intent_name=intent_name, level=SupportLevel.NONE.value
        )
        lang_supports.append(lang_support)

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
            auto_slots: Set[str] = set()
            if data.slots:
                # Inferred slots
                auto_slots.update(data.slots.keys())

            if data.requires_context.get("area", {}).get("slot"):
                # Context area
                auto_slots.add(CONTEXT_AREA_SLOT)

            for sentence in data.sentences:
                sentence_combos: Set[Tuple[str, ...]] = set()
                for _, combo in _get_slots(
                    sentence.expression, data, lang_intents, rule_slot_cache
                ):
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
                    "slots": list(combo),  # type: ignore
                    "sentences": sorted(sentences),  # type: ignore
                }
                for combo, sentences in sorted(combo_sentences.items())
                if combo in extra_combos
            ]
            continue

        lang_support.level = SupportLevel.FULL.value

    return (language, lang_supports)


# -----------------------------------------------------------------------------


def _get_slots(
    e: Expression,
    data: IntentData,
    intents: Intents,
    rule_slot_cache: Dict[Tuple[str, bool], Any],
) -> Iterable[Tuple[bool, Any]]:
    if isinstance(e, Group):
        grp: Group = e
        if isinstance(grp, (Sequence, Permutation)):
            seq_with_slots: List[List[Iterable[Union[str, None]]]] = [[]]
            for item in grp.items:
                for item_has_slot, item_slots in _get_slots(
                    item, data, intents, rule_slot_cache
                ):
                    if not item_has_slot:
                        continue

                    seq_with_slots[-1].append(item_slots)

                if seq_with_slots[-1]:
                    seq_with_slots.append([])

            if not seq_with_slots[-1]:
                seq_with_slots.pop()

            for slot_combo in itertools.product(*seq_with_slots):
                yield (True, slot_combo)
        elif isinstance(grp, Alternative):
            for item in grp.items:
                for item_has_slot, item_slots in _get_slots(
                    item, data, intents, rule_slot_cache
                ):
                    if not item_has_slot:
                        continue

                    yield (True, item_slots)

            if grp.is_optional:
                yield (True, None)
        else:
            raise ValueError(f"Unexpected group type: {grp}")
    elif isinstance(e, ListReference):
        list_ref: ListReference = e
        yield (True, list_ref.slot_name)
    elif isinstance(e, RuleReference):
        rule_ref: RuleReference = e
        rule_body = data.expansion_rules.get(rule_ref.rule_name)
        from_data = True

        if rule_body is None:
            rule_body = intents.expansion_rules[rule_ref.rule_name]
            from_data = False

        if rule_body is None:
            raise ValueError(f"Missing body for expansion rule: {rule_ref.rule_name}")

        cache_key = (rule_ref.rule_name, from_data)
        cached_slots = rule_slot_cache.get(cache_key)
        if cached_slots is None:
            cached_slots = list(
                _get_slots(rule_body.expression, data, intents, rule_slot_cache)
            )
            rule_slot_cache[cache_key] = cached_slots

        yield from cached_slots


def _flatten(items: Iterable[Any]) -> Iterable[str]:
    for item in items:
        if item is None:
            continue

        if isinstance(item, str):
            yield item
        else:
            yield from _flatten(item)
