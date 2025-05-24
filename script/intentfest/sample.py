"""Sample sentences using language intent files."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

import yaml
from hassil import Intents, merge_dict, sample_intents

from shared import get_slot_lists

from .const import LANGUAGES, SENTENCE_DIR, TESTS_DIR
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
        "-n",
        "--max-sentences-per-intent",
        type=int,
        help="Limit number of sentences per intent",
    )
    parser.add_argument(
        "--intents", nargs="+", help="Only sample sentences from these intents"
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    language_dir = SENTENCE_DIR / args.language
    tests_dir = TESTS_DIR / args.language

    # Load test areas and entities for language
    test_names = yaml.safe_load((tests_dir / "_fixtures.yaml").read_text())
    slot_lists = get_slot_lists(test_names)

    # Load intents
    intents_dict: Dict[str, Any] = {}
    for intent_path in language_dir.glob("*.yaml"):
        with open(intent_path, "r", encoding="utf-8") as intent_file:
            merge_dict(intents_dict, yaml.safe_load(intent_file))

    assert intents_dict, "No intent YAML files loaded"
    intents = Intents.from_dict(intents_dict)

    # Sample sentences
    intents_and_texts = sample_intents(
        intents,
        slot_lists,
        max_sentences_per_intent=args.max_sentences_per_intent,
        intent_names=set(args.intents) if args.intents else None,
    )
    for intent_name, sentence_text in intents_and_texts:
        json.dump(
            {"intent": intent_name, "text": sentence_text.strip()},
            sys.stdout,
            ensure_ascii=False,
        )
        print("")

    return 0
