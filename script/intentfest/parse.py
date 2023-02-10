"""Parse sentences using language intent files."""
from __future__ import annotations

import argparse
import json
import sys

from .const import LANGUAGES
from .sentenceParser import SentenceParser
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language",
        required=True,
        type=str,
        choices=LANGUAGES,
        help="The language to validate.",
    )
    parser.add_argument(
        "--sentence",
        required=True,
        action="append",
        type=str,
        help="Sentence(s) to parse",
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()
    sentence_parser = SentenceParser(args.language)

    # Parse sentences
    for sentence in args.sentence:
        sentence_parser.parse(sentence)
        json.dump(
            sentence_parser.get_response_data(),
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )

    return 0
