"""CLI tool for sampling sentences from intents."""
import argparse
import itertools
import json
import logging
import sys
from functools import partial
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple

import yaml

from .expression import (
    Expression,
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    TextChunk,
)
from .intents import Intents, RangeSlotList, SlotList, TextSlotList
from .recognize import MissingListError, MissingRuleError
from .util import merge_dict

_LOGGER = logging.getLogger("hassil.sample")


def sample_intents(
    intents: Intents,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    separator: str = " ",
    max_sentences_per_intent: Optional[int] = None,
    intent_names: Optional[Set[str]] = None,
) -> Iterable[Tuple[str, str]]:
    """Sample text strings for sentences from intents."""
    if slot_lists is None:
        slot_lists = intents.slot_lists
    else:
        # Combine with intents
        slot_lists = {**intents.slot_lists, **slot_lists}

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = intents.expansion_rules
    else:
        # Combine rules
        expansion_rules = {**intents.expansion_rules, **expansion_rules}

    for intent_name, intent in intents.intents.items():
        if intent_names and (intent_name not in intent_names):
            # Skip intent
            continue

        num_intent_sentences = 0
        skip_intent = False

        for intent_data in intent.data:
            for intent_sentence in intent_data.sentences:
                sentence_texts = sample_expression(
                    intent_sentence, slot_lists, expansion_rules, separator
                )
                for sentence_text in sentence_texts:
                    yield (intent_name, sentence_text)
                    num_intent_sentences += 1

                    if (max_sentences_per_intent is not None) and (
                        0 < max_sentences_per_intent <= num_intent_sentences
                    ):
                        skip_intent = True
                        break

                if skip_intent:
                    break

            if skip_intent:
                break


_X = False


def sample_expression(
    expression: Expression,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    separator: str = " ",
) -> Iterable[str]:
    """Sample possible text strings from an expression."""
    if isinstance(expression, TextChunk):
        chunk: TextChunk = expression
        yield chunk.text
    elif isinstance(expression, Sequence):
        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            for item in seq.items:
                yield from sample_expression(
                    item, slot_lists, expansion_rules, separator
                )
        elif seq.type == SequenceType.GROUP:
            seq_sentences = map(
                partial(
                    sample_expression,
                    slot_lists=slot_lists,
                    expansion_rules=expansion_rules,
                    separator=separator,
                ),
                seq.items,
            )
            sentence_texts = itertools.product(*seq_sentences)
            for sentence_words in sentence_texts:
                yield separator.join(filter(None, sentence_words))
        else:
            raise ValueError(f"Unexpected sequence type: {seq}")
    elif isinstance(expression, ListReference):
        # {list}
        list_ref: ListReference = expression
        if (not slot_lists) or (list_ref.list_name not in slot_lists):
            raise MissingListError(f"Missing slot list {{{list_ref.list_name}}}")

        slot_list = slot_lists[list_ref.list_name]
        if isinstance(slot_list, TextSlotList):
            text_list: TextSlotList = slot_list

            if not text_list.values:
                # Not necessarily an error, but may be a surprise
                _LOGGER.warning("No values for list: %s", list_ref.list_name)

            for text_value in text_list.values:
                yield from sample_expression(
                    text_value.text_in,
                    slot_lists,
                    expansion_rules,
                    separator,
                )
        elif isinstance(slot_list, RangeSlotList):
            range_list: RangeSlotList = slot_list
            number_strs = map(
                str, range(range_list.start, range_list.stop + 1, range_list.step)
            )
            yield from number_strs

        else:
            raise ValueError(f"Unexpected slot list type: {slot_list}")
    elif isinstance(expression, RuleReference):
        # <rule>
        rule_ref: RuleReference = expression
        if (not expansion_rules) or (rule_ref.rule_name not in expansion_rules):
            raise MissingRuleError(f"Missing expansion rule <{rule_ref.rule_name}>")

        rule_body = expansion_rules[rule_ref.rule_name]
        yield from sample_expression(
            rule_body,
            slot_lists,
            expansion_rules,
            separator,
        )
    else:
        raise ValueError(f"Unexpected expression: {expression}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml", nargs="+", help="YAML files or directories")
    parser.add_argument(
        "-n",
        "--max-sentences-per-intent",
        type=int,
        help="Limit number of sentences per intent",
    )
    parser.add_argument(
        "--intents", nargs="+", help="Only sample sentences from these intents"
    )
    parser.add_argument(
        "--separator",
        default=" ",
        help="Separator between words in sentences (default: space)",
    )
    parser.add_argument(
        "--areas",
        nargs="+",
        help="Area names",
        default=["area"],
    )
    parser.add_argument(
        "--names", nargs="+", default=["entity"], help="Device/entity names"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)
    _LOGGER.debug(args)

    slot_lists = {
        "area": TextSlotList.from_strings(args.areas),
        "name": TextSlotList.from_strings(args.names),
    }

    input_dict = {"intents": {}}
    for yaml_path_str in args.yaml:
        yaml_path = Path(yaml_path_str)
        if yaml_path.is_dir():
            yaml_file_paths = yaml_path.glob("*.yaml")
        else:
            yaml_file_paths = [yaml_path]

        for yaml_file_path in yaml_file_paths:
            _LOGGER.debug("Loading file: %s", yaml_file_path)
            with open(yaml_file_path, "r", encoding="utf-8") as yaml_file:
                merge_dict(input_dict, yaml.safe_load(yaml_file))

    assert input_dict, "No intent YAML files loaded"
    intents = Intents.from_dict(input_dict)

    intents_and_texts = sample_intents(
        intents,
        slot_lists,
        separator=args.separator,
        max_sentences_per_intent=args.max_sentences_per_intent,
        intent_names=set(args.intents) if args.intents else None,
    )
    for intent_name, sentence_text in intents_and_texts:
        json.dump({"intent": intent_name, "text": sentence_text}, sys.stdout)
        print("")


if __name__ == "__main__":
    main()
