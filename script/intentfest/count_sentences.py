"""Counts the number of possible sentences per intent."""

from __future__ import annotations

import argparse
import math
from functools import reduce
from typing import Any, Dict, Optional

import yaml
from hassil import (
    Alternative,
    Expression,
    Group,
    IntentData,
    Intents,
    ListReference,
    Permutation,
    RangeSlotList,
    RuleReference,
    Sentence,
    Sequence,
    SlotList,
    TextSlotList,
    merge_dict,
    parse_sentence,
)

from .const import LANGUAGES, SENTENCE_DIR
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language",
        type=str,
        choices=LANGUAGES,
        help="The language to validate.",
    )
    parser.add_argument("--intent", type=str, help="Filter by intent")
    parser.add_argument("--sentence", type=str, help="Sentence template to count")
    parser.add_argument(
        "--summary", action="store_true", help="Only show language/intent counts"
    )
    parser.add_argument(
        "--lists-and-ranges",
        action="store_true",
        help="Count possible values for lists/ranges",
    )
    return parser.parse_args()


def get_count(
    e: Expression, intents: Intents, intent_data: IntentData, args: argparse.Namespace
) -> int:
    if isinstance(e, Group):
        grp: Group = e
        item_counts = [
            get_count(item, intents, intent_data, args) for item in grp.items
        ]

        if isinstance(grp, Alternative):
            summed_counts = max(1, sum(item_counts))
            if grp.is_optional:
                summed_counts += 1

            return summed_counts

        if isinstance(grp, (Sequence, Permutation)):
            multiplied_counts = reduce(
                lambda x, y: max(1, x) * max(1, y), item_counts, 1
            )
            if isinstance(grp, Permutation):
                multiplied_counts *= math.factorial(len(item_counts))

            return multiplied_counts

        raise ValueError(f"Unexpected group type: {grp}")

    if args.lists_and_ranges:
        if isinstance(e, ListReference):
            list_ref: ListReference = e
            slot_list: Optional[SlotList] = None

            slot_list = intent_data.slot_lists.get(list_ref.list_name)
            if not slot_list:
                slot_list = intents.slot_lists.get(list_ref.list_name)

            if isinstance(slot_list, TextSlotList):
                text_list: TextSlotList = slot_list
                return max(
                    1,
                    sum(
                        get_count(v.text_in, intents, intent_data, args)
                        for v in text_list.values
                    ),
                )

            if isinstance(slot_list, RangeSlotList):
                range_list: RangeSlotList = slot_list
                if range_list.step == 1:
                    return range_list.stop - range_list.start + 1

                return len(
                    range(range_list.start, range_list.stop + 1, range_list.step)
                )

    if isinstance(e, RuleReference):
        rule_ref: RuleReference = e
        rule_body: Optional[Sentence] = None

        rule_body = intent_data.expansion_rules.get(rule_ref.rule_name)
        if not rule_body:
            rule_body = intents.expansion_rules.get(rule_ref.rule_name)

        if rule_body:
            return get_count(rule_body.expression, intents, intent_data, args)

    return 0


def run() -> int:
    args = get_arguments()

    if args.language:
        languages = [args.language]
    else:
        languages = LANGUAGES

    user_sentence: Optional[Sentence] = None
    if args.sentence:
        user_sentence = parse_sentence(args.sentence, keep_text=True)

    for language in sorted(languages):
        language_dir = SENTENCE_DIR / language

        # Load intents
        intents_dict: Dict[str, Any] = {}
        for intent_path in language_dir.glob("*.yaml"):
            with open(intent_path, "r", encoding="utf-8") as intent_file:
                merge_dict(intents_dict, yaml.safe_load(intent_file))

        assert intents_dict, "No intent YAML files loaded"
        intents = Intents.from_dict(intents_dict)

        counts = []
        for intent in intents.intents.values():
            if args.intent and (intent.name != args.intent):
                continue

            for data_idx, data in enumerate(intent.data):
                if user_sentence:
                    sentences = [user_sentence]
                else:
                    sentences = data.sentences

                for sentence in sentences:
                    counts.append(
                        (
                            intent.name,
                            data_idx,
                            sentence.text,
                            get_count(sentence.expression, intents, data, args),
                        )
                    )

        num_lang_sentences = sum(c[-1] for c in counts)
        print(f"{language}:", f"{num_lang_sentences:,}")

        counts_by_intent = {
            intent_name: sum(c[-1] for c in counts if c[0] == intent_name)
            for intent_name in sorted(intents.intents)
        }
        for intent_name, intent_count in sorted(
            counts_by_intent.items(), key=lambda kv: kv[1], reverse=True
        ):
            if args.intent and (intent_name != args.intent):
                continue

            intent = intents.intents[intent_name]
            print(f"-- {intent_name}:", f"{intent_count:,}")

            if args.summary:
                continue

            counts_by_data = {
                data_idx: sum(
                    c[-1]
                    for c in counts
                    if (c[0] == intent_name) and (c[1] == data_idx)
                )
                for data_idx in range(len(intent.data))
            }
            for data_idx, data_count in counts_by_data.items():
                data = intent.data[data_idx]
                print(f"---- data {data_idx + 1}:", f"{data_count:,}")
                for count in counts:
                    if (count[0] != intent_name) or (count[1] != data_idx):
                        continue

                    sentence_text, sentence_count = count[2], count[3]
                    print(f"------ {sentence_text}", f"{sentence_count:,}")

    return 0
