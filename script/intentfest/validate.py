"""Validate all intent files."""
from __future__ import annotations

import argparse
import re
from typing import Any

import voluptuous as vol
import yaml
from voluptuous.humanize import validate_with_humanized_errors

from .const import INTENTS_FILE, LANGUAGES, RESPONSE_DIR, ROOT, SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser, require_sentence_domain_slot

# Slots can be {name} or {name:new_name}
PATTERN_SLOTS = re.compile(r"\{(?P<name>[a-z_]+)(?:|:\w+)\}")
PATTERN_EXPANSION_RULES = re.compile(r"\<(?P<name>[a-z_]+)\>")


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
            vol.Optional("slot_combinations"): {
                str: [str],
            },
            vol.Optional("response_variables"): {
                str: {
                    vol.Required("description"): str,
                }
            },
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
                vol.Required("data"): [
                    {
                        vol.Required("sentences"): [str],
                        vol.Optional("slots"): {
                            str: match_anything,
                        },
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
                            {
                                "in": str,
                                "out": match_anything,
                            },
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
            vol.Optional("errors"): {
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
                        str: vol.Any(
                            {vol.Required("value"): match_anything},
                            int,
                            float,
                            str,
                        ),
                    },
                },
            }
        ],
    }
)

TESTS_COMMON = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("areas"): [
            {
                vol.Required("name"): str,
                vol.Required("id"): str,
            }
        ],
        vol.Optional("entities"): [
            {
                vol.Required("name"): str,
                vol.Required("id"): str,
                vol.Required("area"): str,
                vol.Required("domain"): str,
            }
        ],
    }
)

RESPONSE_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("responses"): {
            vol.Optional("intents"): {
                str: {vol.Required("success"): [str]},
            }
        },
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
    sentence_dir = SENTENCE_DIR / language
    test_dir = TESTS_DIR / language
    response_dir = RESPONSE_DIR / language

    sentence_files = {}
    lists = {}
    expansion_rules = {}

    for sentence_file in sentence_dir.iterdir():
        path = str(sentence_dir / sentence_file.name)
        content = yaml.safe_load(sentence_file.read_text())
        sentence_files[sentence_file.name] = content

        try:
            validate_with_humanized_errors(content, SENTENCE_SCHEMA)
        except vol.Error as err:
            errors[language].append(f"{path}: invalid format: {err}")
            continue

        if content["language"] != language:
            errors[language].append(
                f"{path}: references incorrect language {content['language']}"
            )

        if "lists" in content:
            lists.update(content["lists"])

        if "expansion_rules" in content:
            expansion_rules.update(content["expansion_rules"])

    for sentence_file, content in sentence_files.items():
        if sentence_file.startswith("_"):
            if "intents" in content:
                errors[language].append(
                    f"{path}: is a common file and should not contain intents"
                )
            continue

        domain, intent = sentence_file.split(".")[0].split("_")

        if intent not in intent_schemas:
            errors[language].append(
                f"{path}: Filename references unknown intent {intent}.yaml"
            )
            continue

        for intent_name, intent_info in content["intents"].items():
            if intent != intent_name:
                errors[language].append(
                    f"{path}: references incorrect intent {intent_name}. Only {intent} allowed"
                )
                continue

            intent_slots = intent_schemas[intent].get("slots", {})
            intent_slots_plus_lists = {*intent_slots, *lists}

            for idx, sentence_info in enumerate(intent_info["data"]):
                prefix = f"{path} sentence block {idx + 1}:"
                slots = sentence_info.get("slots", {})

                for sentence in sentence_info["sentences"]:
                    for slot in PATTERN_SLOTS.findall(sentence):
                        if slot not in intent_slots_plus_lists:
                            errors[language].append(
                                f"{prefix} sentence '{sentence}' references unknown slot '{slot}'"
                            )
                        continue

                    for expansion_rule in PATTERN_EXPANSION_RULES.findall(sentence):
                        for slot in PATTERN_SLOTS.findall(
                            expansion_rules[expansion_rule]
                        ):
                            if slot not in intent_slots_plus_lists:
                                errors[language].append(
                                    f"{prefix} sentence '{sentence}' references expansion rule '{expansion_rule}' which references unknown slot '{slot}'"
                                )
                            continue

                for slot in slots:
                    if slot not in intent_slots:
                        errors[language].append(
                            f"{prefix} references unknown slot {slot}"
                        )

                if require_sentence_domain_slot(intent, domain) and domain != slots.get(
                    "domain"
                ):
                    errors[language].append(
                        f"{prefix} expected domain slot for {domain}, "
                        f"got {slots.get('domain')}"
                    )

    for test_file in test_dir.iterdir():
        path = str(test_dir.relative_to(ROOT) / test_file.name)

        if test_file.name not in sentence_files:
            errors[language].append(f"{path}: has no matching sentence file")
            continue

        sentence_files.pop(test_file.name)

        content = yaml.safe_load(test_file.read_text())

        if test_file.name == "_common.yaml":
            schema = TESTS_COMMON
        else:
            schema = TESTS_SCHEMA

        try:
            validate_with_humanized_errors(content, schema)
        except vol.Error as err:
            errors[language].append(f"{path}: invalid format: {err}")
            continue

        if content["language"] != language:
            errors[language].append(
                f"{path}: references incorrect language {content['language']}"
            )

        if test_file.name == "_common.yaml":
            continue

        domain, intent = test_file.stem.split("_")

        tested_intents = set(i["intent"]["name"] for i in content["tests"])

        if intent not in tested_intents:
            errors[language].append(
                f"{path}: does not contain test for intent {intent}"
            )

        if extra_intents := tested_intents - {intent}:
            errors[language].append(
                f"{path}: tests extra intents {', '.join(sorted(extra_intents))}. Only {intent} allowed"
            )

    if sentence_files:
        for sentence_file in sentence_files:
            errors[language].append(f"{sentence_file} has no tests")

    for response_file in response_dir.iterdir():
        path = str(response_dir / response_file.name)
        content = yaml.safe_load(response_file.read_text())

        try:
            validate_with_humanized_errors(content, RESPONSE_SCHEMA)
        except vol.Error as err:
            errors[language].append(f"{path}: invalid format: {err}")
            continue

        if content["language"] != language:
            errors[language].append(
                f"{path}: references incorrect language {content['language']}"
            )

        domain, intent = response_file.stem.split("_")

        for intent_name, intent_info in content["responses"]["intents"].items():
            if intent != intent_name:
                errors[language].append(
                    f"{path}: references incorrect intent {intent_name}. Only {intent} allowed"
                )
                continue
