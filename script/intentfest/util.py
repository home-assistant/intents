"""Translation utils."""
import argparse
from typing import Any, Dict

import yaml
from hassil.intents import SlotList, TextSlotList
from hassil.util import merge_dict

from .const import RESPONSE_DIR, SENTENCE_DIR


# pylint:disable=too-many-ancestors
class YamlDumper(yaml.Dumper):
    """Subclassed dumper to ensure correct indentation."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


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


def get_slot_lists(test_names: Dict[str, Any]) -> Dict[str, SlotList]:
    # Load test areas and entities for language
    return {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in test_names["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (
                entity["name"],
                entity["id"],
                {"domain": entity["id"].split(".", maxsplit=1)[0]},
            )
            for entity in test_names["entities"]
        ),
    }
