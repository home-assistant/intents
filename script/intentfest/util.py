"""Translation utils."""
import argparse


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Home Assistant Translations")
    parser.add_argument(
        "action",
        type=str,
        choices=[
            "add_language",
            "parse",
            "sample_template",
            "sample",
            "validate",
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
