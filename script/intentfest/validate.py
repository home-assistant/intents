"""Validate all intent files."""
from __future__ import annotations

import argparse
from typing import Any

import voluptuous as vol
import yaml
from voluptuous.humanize import validate_with_humanized_errors

from .const import INTENTS_FILE, LANGUAGES, SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser, require_sentence_domain_slot


def match_anything(value):
    """Validator that matches everything"""
    return value


def single_key_dict_validator(schemas: dict[str, Any]) -> vol.Schema:
    """Create a validator for a single key dict."""

    def validate(value):
        if not isinstance(value, dict):
            raise vol.Invalid("Expected a dict")

        if len(value) != 1:
            raise vol.Invalid("Expected a single key dict")

        key = next(iter(value))

        if key not in schemas:
            raise vol.Invalid(f"Expected a key in {', '.join(schemas)}")

        if not isinstance(schemas[key], vol.Schema):
            schemas[key] = vol.Schema(schemas[key])

        return schemas[key](value[key])

    return validate


INTENTS_SCHEMA = vol.Schema(
    {
        str: {
            vol.Required("description"): str,
            vol.Optional("slots"): {
                str: {
                    vol.Required("description"): str,
                    vol.Optional("required"): bool,
                }
            },
            vol.Optional("slot_combinations"): {str: [str]},
        }
    }
)

INTENT_ERRORS = {
    "no_intent",
    "no_area",
    "no_domain",
    "no_device_class",
    "no_entity",
    "handle_error",
}

SENTENCE_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("intents"): {
            str: {
                "data": [
                    {
                        vol.Required("sentences"): [str],
                        vol.Optional("slots"): {str: match_anything},
                    }
                ]
            }
        },
        vol.Optional("lists"): {
            str: single_key_dict_validator(
                {
                    "values": [
                        vol.Any(
                            str,
                            {"in": str, "out": match_anything},
                        )
                    ],
                    "range": {
                        vol.Required("type", default="number"): str,
                        vol.Required("from"): int,
                        vol.Required("to"): int,
                        vol.Optional("step", default=1): int,
                    },
                }
            )
        },
        vol.Optional("expansion_rules"): {str: str},
        vol.Optional("skip_words"): [str],
        vol.Optional("responses"): {
            "errors": {
                vol.In(INTENT_ERRORS): str,
            }
        },
    }
)

TESTS_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Required("tests"): [
            {
                vol.Required("sentences"): [str],
                vol.Required("intent"): {
                    vol.Required("name"): str,
                    vol.Optional("slots"): {
                        str: {vol.Required("value"): match_anything}
                    },
                },
            }
        ],
    }
)


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language", type=str, choices=LANGUAGES, help="The language to validate."
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    if args.language is None:
        languages = LANGUAGES
    else:
        languages = [args.language]

    intent_schemas = yaml.safe_load(INTENTS_FILE.read_text())

    try:
        validate_with_humanized_errors(intent_schemas, INTENTS_SCHEMA)
    except vol.Error as err:
        print(f"File intents.yaml has invalid format: {err}")
        return 1

    errors: dict[str, list[str]] = {}

    for language in languages:
        errors[language] = []
        validate_language(intent_schemas, language, errors)
        # Remove language if no errors
        if not errors[language]:
            errors.pop(language)

    if errors:
        print("Validation failed")
        print()

        for language, language_errors in errors.items():
            print(f"Language: {language}")
            for error in language_errors:
                print(f" - {error}")
            print()
        return 1

    print("All good!")
    return 0


def validate_language(intent_schemas, language, errors):
    language_dir = SENTENCE_DIR / language
    test_dir = TESTS_DIR / language

    language_files = set()

    for language_file in language_dir.iterdir():
        language_files.add(language_file.name)

        content = yaml.safe_load(language_file.read_text())

        try:
            validate_with_humanized_errors(content, SENTENCE_SCHEMA)
        except vol.Error as err:
            errors[language].append(
                f"File {language_file.name} has invalid format: {err}"
            )
            continue

        if content["language"] != language:
            errors[language].append(
                f"File {language_file.name} references incorrect language {content['language']}"
            )

        if language_file.name.startswith("_"):
            continue

        domain, intent = language_file.stem.split("_")

        if intent not in intent_schemas:
            errors[language].append(
                f"Filename {language_file.name} references unknown intent {intent}.yaml"
            )
            continue

        if content["language"] != language:
            errors[language].append(
                f"File {language_file.name} references incorrect language {content['language']}"
            )

        for intent_name, intent_info in content["intents"].items():
            if intent != intent_name:
                errors[language].append(
                    f"File {language_file.name} references incorrect intent {intent_name}. Only {intent} allowed"
                )
                continue

            for idx, sentence_info in enumerate(intent_info["data"]):
                prefix = f"{language_file.name} sentence block {idx + 1}"
                slots = sentence_info.get("slots", {})
                if require_sentence_domain_slot(intent, domain) and domain != slots.get(
                    "domain"
                ):
                    errors[language].append(
                        f"{prefix} expected domain slot for {domain}, "
                        f"got {slots.get('domain')}"
                    )

    for test_file in test_dir.iterdir():
        if test_file.name not in language_files:
            errors[language].append(
                f"Test file {test_file.name} references unknown sentence file"
            )
            continue

        language_files.discard(test_file.name)

        content = yaml.safe_load(test_file.read_text())

        if content["language"] != language:
            errors[language].append(
                f"Test {test_file.name} references incorrect language {content['language']}"
            )

        if test_file.name == "_common.yaml":
            continue

        try:
            validate_with_humanized_errors(content, TESTS_SCHEMA)
        except vol.Error as err:
            errors[language].append(f"File {test_file.name} has invalid format: {err}")
            continue

        domain, intent = test_file.stem.split("_")

        tested_intents = set(i["intent"]["name"] for i in content["tests"])

        if intent not in tested_intents:
            errors[language].append(
                f"Test {test_file.name} should have tests for {intent}"
            )

        if extra_intents := tested_intents - {intent}:
            errors[language].append(
                f"Test {test_file.name} references incorrect intents {', '.join(sorted(extra_intents))}. Only {intent} allowed"
            )

    if language_files:
        for language_file in language_files:
            errors[language].append(f"{language_file} has no tests")
