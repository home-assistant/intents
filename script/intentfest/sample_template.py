"""Sample possible sentences from a template."""

from __future__ import annotations

import argparse
from typing import Dict

from hassil import parse_sentence
from hassil.expression import Sentence
from hassil.intents import RangeSlotList, SlotList, TextSlotList
from hassil.sample import sample_expression

from .const import LANGUAGES
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "template",
        type=str,
        help="Sentence template",
    )
    parser.add_argument(
        "--values",
        nargs="+",
        action="append",
        metavar=("name", "value"),
        help="Add values from a list",
    )
    parser.add_argument(
        "--range",
        nargs=3,
        action="append",
        metavar=("name", "start", "stop"),
        help="Add range list",
    )
    parser.add_argument(
        "--rule",
        nargs=2,
        action="append",
        metavar=("name", "body"),
        help="Add expansion rule",
    )
    parser.add_argument(
        "--language",
        type=str,
        choices=LANGUAGES,
        help="The language to validate.",
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    slot_lists: Dict[str, SlotList] = {}
    expansion_rules: Dict[str, Sentence] = {}

    if args.values:
        for name_and_values in args.values:
            name, values = name_and_values[0], name_and_values[1:]
            slot_lists[name] = TextSlotList.from_strings(values)

    if args.range:
        for name_and_args in args.range:
            name, start, stop = (
                name_and_args[0],
                int(name_and_args[1]),
                int(name_and_args[2]),
            )
            slot_lists[name] = RangeSlotList(name, start, stop)

    if args.rule:
        for name, body in args.rule:
            expansion_rules[name] = parse_sentence(body)

    template = parse_sentence(args.template)
    for sentence in sample_expression(
        template,
        slot_lists=slot_lists,
        expansion_rules=expansion_rules,
        language=args.language,
    ):
        print(sentence.strip())

    return 0
