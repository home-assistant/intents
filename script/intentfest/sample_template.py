"""Sample possible sentences from a template."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from hassil.parse import parse_sentence
from hassil.sample import sample_expression
from hassil.intents import SlotList, TextSlotList, RangeSlotList
from hassil.expression import Sentence

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
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    template = parse_sentence(args.template)
    for sentence in sample_expression(template):
        print(sentence)

    return 0
