"""Generate a map for day numbers to ordinal words."""

from __future__ import annotations

import argparse
import json
from typing import Dict

from unicode_rbnf import RbnfEngine, RulesetName

from .const import LANGUAGES
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
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    engine = RbnfEngine.for_language(args.language)
    ordinals: Dict[int, str] = {}
    for day in range(1, 32):
        ordinals[day] = engine.format_number(day, ruleset_name=RulesetName.ORDINAL)

    print(json.dumps(ordinals, ensure_ascii=False, indent=2))

    return 0
