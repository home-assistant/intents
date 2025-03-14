"""Command to generate merged output."""

import argparse
import json
from pathlib import Path

import yaml
from hassil import merge_dict

from .const import INTENTS_FILE, LANGUAGES, RESPONSE_DIR, SENTENCE_DIR
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument("target", type=str, help="The target directory.")
    return parser.parse_args()


def run() -> int:
    args = get_arguments()
    target = Path(args.target)

    intent_info = yaml.safe_load(INTENTS_FILE.read_text())
    intent_by_domain: dict[str, list] = {}
    for intent, info in intent_info.items():
        if not info.get("supported", True):
            continue
        intent_by_domain.setdefault(info["domain"], []).append(intent)

    for domain in intent_by_domain:
        (target / domain).mkdir(parents=True, exist_ok=True)

    for language in LANGUAGES:
        merged_sentences: dict = {}
        for sentence_file in (SENTENCE_DIR / language).iterdir():
            merge_dict(merged_sentences, yaml.safe_load(sentence_file.read_text()))

        merged_responses: dict = {}
        for response_file in (RESPONSE_DIR / language).iterdir():
            merge_dict(merged_responses, yaml.safe_load(response_file.read_text()))

        for domain, supported_intents in intent_by_domain.items():
            domain_intents = {}
            for intent, info in merged_sentences["intents"].items():
                if intent not in supported_intents:
                    continue

                data = []
                for data_set in info["data"]:
                    if len(data_set["sentences"]) > 0:
                        data.append(data_set)

                if data:
                    domain_intents[intent] = {
                        **info,
                        "data": data,
                    }

            domain_responses = {
                intent: info
                for intent, info in merged_responses["responses"]["intents"].items()
                if intent in supported_intents
            }

            if not domain_intents and not domain_responses:
                continue

            if domain == "homeassistant":
                output: dict = {
                    **merged_sentences,
                    "intents": {},
                }
            else:
                output = {"language": language}

            if domain_intents:
                output["intents"] = domain_intents

            if domain_responses:
                output.setdefault("responses", {})["intents"] = domain_responses

            # Write as JSON
            target_path = target / domain / f"{language}.json"
            with target_path.open("w", encoding="utf-8") as target_file:
                json.dump(output, target_file, ensure_ascii=False, indent=2)

    return 0
