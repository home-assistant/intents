"""Translation utils."""
import argparse

import yaml
from hassil.util import merge_dict

from .const import RESPONSE_DIR, SENTENCE_DIR


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Home Assistant Translations")
    parser.add_argument(
        "action",
        type=str,
        choices=[
            "add_language",
            "codeowners",
            "merged_output",
            "parse",
            "sample_template",
            "sample",
            "website_summary",
            "validate",
            "language_table",
        ],
    )
    parser.add_argument("--debug", action="store_true", help="Enable log output")
    return parser


def require_sentence_domain_slot(intent, domain):
    """Return if sentence definition requires a domain slot for intent."""
    return domain != "homeassistant" and intent in (
        "HassTurnOn",
        "HassTurnOff",
        "HassToggle",
    )


def load_merged_sentences(language: str) -> dict:
    merged_sentences: dict = {}
    for sentence_file in (SENTENCE_DIR / language).iterdir():
        merge_dict(merged_sentences, yaml.safe_load(sentence_file.read_text()))
    return merged_sentences


def load_merged_responses(language: str) -> dict:
    merged_responses: dict = {}
    for response_file in (RESPONSE_DIR / language).iterdir():
        merge_dict(merged_responses, yaml.safe_load(response_file.read_text()))
    return merged_responses
