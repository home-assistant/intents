"""Validate all intent files."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import voluptuous as vol
import yaml
from voluptuous.humanize import validate_with_humanized_errors

from .const import INTENTS_FILE, LANGUAGES, RESPONSE_DIR, ROOT, SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser, require_sentence_domain_slot


def match_anything(value):
    """Validator that matches everything"""
    return value


def match_anything_but_dict(value):
    """Validator that matches everything but a dict"""
    if isinstance(value, dict):
        raise vol.Invalid("Expected anythung but a dictionary")
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

SENTENCE_MATCHER = vol.Match(
    r"^[\w \|\(\)\[\]\{\}\<\>]+$",
    msg="Sentences should only contain words and matching syntax. They should not contain punctuation.",
)

SENTENCE_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("intents"): {
            str: {
                vol.Required("data"): [
                    {
                        vol.Required("sentences"): [SENTENCE_MATCHER],
                        vol.Optional("slots"): {
                            str: match_anything,
                        },
                    }
                ]
            }
        },
    }
    # Fields from SENTENCE_COMMON_SCHEMA are allowed by the parser
    # but we do not accept that in our repository.
)

SENTENCE_COMMON_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("responses"): {
            vol.Optional("errors"): {
                vol.In(INTENT_ERRORS): str,
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
                            match_anything_but_dict,
                        ),
                    },
                },
            }
        ],
    }
)

TESTS_FIXTURES = vol.Schema(
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


def _load_yaml_file(
    errors: list, language: str, file_path: Path, schema: vol.Schemna
) -> dict | None:
    """Load a YAML file."""
    path = str(file_path.relative_to(ROOT))
    try:
        content = yaml.safe_load(file_path.read_text())
    except yaml.YAMLError as err:
        errors.append(f"{path}: invalid YAML: {err}")
        return None

    try:
        validate_with_humanized_errors(content, schema)
    except vol.Error as err:
        errors.append(f"{path}: invalid format: {err}")
        return None

    if content["language"] != language:
        errors.append(f"{path}: references incorrect language {content['language']}")
        return None

    return content


def validate_language(intent_schemas, language, errors):
    sentence_dir: Path = SENTENCE_DIR / language
    test_dir: Path = TESTS_DIR / language
    response_dir: Path = RESPONSE_DIR / language

    sentence_files = {}

    for sentence_file in sentence_dir.iterdir():
        path = str(sentence_file.relative_to(ROOT))

        if sentence_file.name == "_common.yaml":
            schema = SENTENCE_COMMON_SCHEMA
        else:
            schema = SENTENCE_SCHEMA

        content = _load_yaml_file(errors[language], language, sentence_file, schema)

        if sentence_file.name == "_common.yaml":
            continue

        sentence_files[sentence_file.name] = content

        if content is None:
            continue

        domain, intent = sentence_file.stem.split("_")

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

            for idx, sentence_info in enumerate(intent_info["data"]):
                prefix = f"{path} sentence block {idx + 1}:"
                slots = sentence_info.get("slots", {})

                if require_sentence_domain_slot(intent, domain) and domain != slots.get(
                    "domain"
                ):
                    errors[language].append(
                        f"{prefix} expected domain slot for {domain}, "
                        f"got {slots.get('domain')}"
                    )

    if not test_dir.exists():
        errors[language].append(f"Missing tests directory {test_dir}")
        return

    for test_file in test_dir.iterdir():
        path = str(test_file.relative_to(ROOT))

        if test_file.name == "_fixtures.yaml":
            schema = TESTS_FIXTURES
        else:
            schema = TESTS_SCHEMA

        content = _load_yaml_file(errors[language], language, test_file, schema)

        if content is None or test_file.name == "_fixtures.yaml":
            area_ids = set(area["id"] for area in content.get("areas", []))
            for entity in content.get("entities", []):
                if entity["area"] not in area_ids:
                    errors[language].append(
                        f"{path}: Entity {entity['name']} references unknown area {entity['id']}"
                    )
            continue

        if test_file.name not in sentence_files:
            errors[language].append(f"{path}: has no matching sentence file")
            continue

        sentence_content = sentence_files.pop(test_file.name)
        domain, intent = test_file.stem.split("_")

        test_count = sum(len(test["sentences"]) for test in content["tests"])

        # Happens if the sentence file is invalid
        if sentence_content is None:
            continue

        if intent in sentence_content["intents"]:
            sentence_count = sum(
                len(data["sentences"])
                for data in sentence_content["intents"][intent]["data"]
            )

            if sentence_count > test_count:
                errors[language].append(f"{path}: not all sentences have tests")

    if sentence_files:
        for sentence_file in sentence_files:
            errors[language].append(f"{sentence_file} has no tests")

    for response_file in response_dir.iterdir():
        path = str(response_file.relative_to(ROOT))
        intent = response_file.stem

        if intent not in intent_schemas:
            errors[language].append(
                f"{path}: Filename references unknown intent {response_file.stem}"
            )
            continue

        content = _load_yaml_file(
            errors[language], language, response_file, RESPONSE_SCHEMA
        )

        if content is None:
            continue

        for intent_name, intent_info in content["responses"]["intents"].items():
            if intent != intent_name:
                errors[language].append(
                    f"{path}: references incorrect intent {intent_name}. Only {intent} allowed"
                )
