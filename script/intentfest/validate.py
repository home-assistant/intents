"""Validate all intent files."""

from __future__ import annotations

import argparse
import itertools
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2
import regex
import voluptuous as vol
import yaml
from hassil import (
    Alternative,
    Expression,
    Group,
    ListReference,
    RuleReference,
    parse_sentence,
)
from voluptuous.humanize import validate_with_humanized_errors

from shared import get_jinja2_environment

from .const import (
    INTENTS_FILE,
    LANGUAGES,
    LANGUAGES_FILE,
    LIST_DIR,
    RESPONSE_DIR,
    ROOT,
    RULE_DIR,
    SENTENCE_DIR,
    TESTS_DIR,
)
from .util import get_base_arg_parser

HA_LIST_NAMES = {"name", "area", "floor"}
SLOT_COMBO_VALIDATION_LANGUAGES = {"en"}


def match_anything(value):
    """Validator that matches everything"""
    return value


def match_anything_but_dict(value):
    """Validator that matches everything but a dict"""
    if isinstance(value, dict):
        raise vol.Invalid("Expected anything but a dictionary")
    return value


def match_unicode_regex(pattern: str):
    """Validator that matches a regex with support for Unicode properties."""

    def inner_match(value):
        if regex.match(pattern, value) is None:
            raise vol.Invalid(f"{value} did not match pattern {pattern}")

        return value

    return inner_match


def single_key_dict_validator(schemas: dict[str, Any]) -> Callable[[Any], vol.Schema]:
    """Create a validator for a single key dict."""

    def validate(value) -> vol.Schema:
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


LANGUAGES_SCHEMA = vol.Schema(
    {
        str: {
            vol.Required("nativeName"): str,
            vol.Optional("isRTL"): bool,
            vol.Optional("leaders"): [str],
            vol.Optional("support"): {
                str: {
                    vol.Optional("speech-to-text"): {
                        vol.Optional("speech-to-phrase"): bool,
                        vol.Optional("whisper"): bool,
                        vol.Optional("cloud"): bool,
                    },
                    vol.Optional("text-to-speech"): {
                        vol.Optional("piper"): bool,
                        vol.Optional("cloud"): bool,
                    },
                }
            },
        }
    }
)

INTENTS_SCHEMA = vol.Schema(
    {
        str: {
            vol.Optional("supported"): bool,
            vol.Required("domain"): str,
            vol.Required("description"): str,
            vol.Optional("slots"): {
                # slot name
                str: {
                    vol.Required("description"): str,
                    vol.Optional("required"): bool,
                }
            },
            vol.Required("slot_combinations"): {
                # slot name
                str: {
                    vol.Required("description"): str,
                    vol.Required("importance"): vol.Any(
                        "required", "usable", "complete", "optional"
                    ),
                    vol.Required("slots"): [str],
                    vol.Optional("inferred_domain"): str,
                    vol.Optional("name_domains"): [str],
                    vol.Optional("context_area"): bool,
                    vol.Required("example"): vol.Any(str, [str]),
                    vol.Optional("wildcard_slots"): [str],
                }
            },
            vol.Optional("response_variables"): {
                # variable name
                str: {
                    vol.Required("description"): str,
                }
            },
        }
    }
)

INTENT_ERRORS = {
    "no_intent",
    "handle_error",
    "no_area",
    "no_floor",
    "no_domain",
    "no_domain_in_area",
    "no_domain_in_floor",
    "no_device_class",
    "no_device_class_in_area",
    "no_device_class_in_floor",
    "no_entity",
    "no_entity_in_area",
    "no_entity_in_floor",
    "no_entity_exposed",
    "no_entity_in_area_exposed",
    "no_entity_in_floor_exposed",
    "no_domain_exposed",
    "no_domain_in_area_exposed",
    "no_domain_in_floor_exposed",
    "no_device_class_exposed",
    "no_device_class_in_area_exposed",
    "no_device_class_in_floor_exposed",
    "duplicate_entities",
    "duplicate_entities_in_area",
    "duplicate_entities_in_floor",
    "entity_wrong_state",
    "feature_not_supported",
    "timer_not_found",
    "multiple_timers_matched",
    "no_timer_support",
}

SENTENCE_MATCHER = vol.All(
    match_unicode_regex(r"^[\w\p{M} :\-'\|\(\)\[\]\{\}\<\>;]+$"),
    msg="Sentences should only contain words and matching syntax. They should not contain punctuation.",
)

SENTENCE_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("intents"): {
            str: {
                vol.Required("data"): [
                    {
                        vol.Optional("expansion_rules"): {str: str},
                        vol.Required("sentences"): [SENTENCE_MATCHER],
                        vol.Optional("slots"): {
                            str: match_anything,
                        },
                        vol.Optional("requires_context"): {str: match_anything},
                        vol.Optional("excludes_context"): {str: match_anything},
                        vol.Optional("response"): str,
                        vol.Optional("required_keywords"): [str],
                    }
                ]
            }
        },
    }
    # Fields from SENTENCE_COMMON_SCHEMA are allowed by the parser
    # but we do not accept that in our repository.
)


# pylint: disable=too-many-positional-arguments
def SLOT_COMBO_SENTENCE_SCHEMA(
    language: str,
    combo_name: str,
    available_list_names: set[str],
    available_slot_names: set[str],
    available_rule_names: set[str],
    available_response_names: set[str],
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("language"): language,
            vol.Required("sentences"): [
                vol.All(
                    non_empty_string,
                    not_optional,
                    no_alternative_list_references,
                    allowed_list_names(available_list_names),
                    required_slots_names(available_slot_names),
                    allowed_rule_names(available_rule_names),
                )
            ],
            vol.Optional("response"): vol.In(available_response_names),
        }
    )


SENTENCE_COMMON_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("settings"): {
            vol.Optional("ignore_whitespace"): bool,
            vol.Optional("filter_with_regex"): bool,
        },
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
                                vol.Required("in"): str,
                                vol.Required("out"): match_anything,
                            },
                        )
                    ],
                    "range": {
                        vol.Required("type", default="number"): str,
                        vol.Required("from"): int,
                        vol.Required("to"): int,
                        vol.Optional("step", default=1): int,
                        vol.Optional("fractions"): vol.Any("halves", "tenths"),
                    },
                    "wildcard": bool,
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
                        # In the future, if we want to allow a dictionary,
                        # we should wrap it in a dictionary with {"value": ...}
                        # this will allow us to add more keys in the future.
                        str: match_anything_but_dict,
                    },
                    vol.Optional("context"): {
                        str: match_anything_but_dict,
                    },
                },
                vol.Optional("response"): vol.Any(str, [str]),
            }
        ],
    }
)

TESTS_FIXTURES = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("floors"): [
            {
                vol.Required("name"): str,
                vol.Required("id"): str,
            }
        ],
        vol.Optional("areas"): [
            {
                vol.Required("name"): str,
                vol.Required("id"): str,
                vol.Optional("floor"): str,
            }
        ],
        vol.Optional("entities"): [
            {
                vol.Required("name"): str,
                vol.Required("id"): str,
                vol.Optional("area"): str,
                vol.Optional("device_class"): str,
                vol.Optional("state"): vol.Any(
                    str, {vol.Required("in"): str, vol.Required("out"): str}
                ),
                vol.Optional("attributes"): {str: match_anything},
            }
        ],
        vol.Optional("timers"): [
            {
                vol.Required(
                    vol.Any("start_hours", "start_minutes", "start_seconds")
                ): int,
                vol.Required("total_seconds_left"): int,
                vol.Required("rounded_hours_left"): int,
                vol.Required("rounded_minutes_left"): int,
                vol.Required("rounded_seconds_left"): int,
                vol.Optional("name"): str,
                vol.Optional("area"): str,
                vol.Optional("is_active"): bool,
            }
        ],
    }
)

TESTS_FAILURES = vol.Schema(
    {vol.Required("language"): str, vol.Required("sentences"): [str]}
)


RESPONSE_SCHEMA = vol.Schema(
    {
        vol.Required("language"): str,
        vol.Optional("responses"): {
            vol.Optional("intents"): {
                # intent -> response key -> Jinja2 template
                str: {str: str},
            }
        },
    }
)


def EXPANSION_RULES_SCHEMA(language: str, rule_name: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("language"): language,
            vol.Required(rule_name): vol.All(
                non_empty_string, not_optional, no_list_or_rule_references
            ),
        }
    )


def SHARED_LISTS_SCHEMA(list_name: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(list_name): vol.Any(
                {
                    # Range of numbers
                    vol.Required("range"): {
                        vol.Required("from"): int,
                        vol.Required("to"): int,
                        vol.Optional("step"): int,
                        vol.Optional("type"): "percentage",
                        vol.Optional("fractions"): "halves",
                    }
                },
                {vol.Required("wildcard"): bool},
            )
        },
    )


def LANGUAGE_LISTS_SCHEMA(language: str, list_name: str) -> vol.Schema:

    return vol.Schema(
        {
            vol.Required("language"): language,
            vol.Required(list_name): vol.Any(
                {
                    # Fixed values
                    vol.Required("values"): [
                        vol.Any(
                            vol.All(
                                non_empty_string,
                                not_optional,
                                no_list_or_rule_references,
                            ),
                            {
                                vol.Required("in"): vol.All(
                                    non_empty_string,
                                    not_optional,
                                    no_list_or_rule_references,
                                ),
                                vol.Required("out"): vol.Any(str, int),
                            },
                        )
                    ]
                },
                {
                    # Range of numbers
                    vol.Required("range"): {
                        vol.Required("from"): int,
                        vol.Required("to"): int,
                        vol.Optional("step"): int,
                        vol.Optional("type"): "percentage",
                        vol.Optional("fractions"): "halves",
                    }
                },
                {vol.Required("wildcard"): bool},
            ),
        }
    )


def SLOT_COMBO_TEST_SCHEMA(
    language: str,
    available_slot_names: set[str],
) -> vol.Schema:

    return vol.Schema(
        {
            vol.Required("language"): language,
            vol.Optional("entities"): [
                {
                    vol.Required("name"): str,
                    vol.Required("domain"): str,
                    vol.Optional("state"): str,
                    vol.Optional("state_with_unit"): str,
                }
            ],
            vol.Optional("areas"): [{vol.Required("name"): str}],
            vol.Optional("floors"): [{vol.Required("name"): str}],
            vol.Required("tests"): [
                {
                    vol.Required("sentences"): [str],
                    vol.Required("response"): str,
                    vol.Optional("slots"): {
                        # slot name
                        vol.In(available_slot_names): vol.Any(str, int, [str])
                    },
                    vol.Optional("timers"): [
                        {
                            vol.Optional("start_hours"): int,
                            vol.Optional("start_minutes"): int,
                            vol.Optional("start_seconds"): int,
                            vol.Optional("total_seconds_left"): int,
                            vol.Optional("rounded_hours_left"): int,
                            vol.Optional("rounded_minutes_left"): int,
                            vol.Optional("rounded_seconds_left"): int,
                            vol.Optional("name"): str,
                            vol.Optional("area"): str,
                            vol.Optional("is_active"): bool,
                        }
                    ],
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

    load_errors: list[str] = []

    # intents.yaml
    intent_schemas = _load_yaml_file(load_errors, None, INTENTS_FILE, INTENTS_SCHEMA)
    if intent_schemas:
        # Verify that slot combinations refer only to slots that the intent supports
        for intent_name, intent_info in intent_schemas.items():
            valid_slot_names = set(intent_info.get("slots", []))

            for combo_name, combo_info in intent_schemas[intent_name][
                "slot_combinations"
            ].items():
                error_info = f"intent_name={intent_name}, combo_name={combo_name}"
                combo_slot_names = set(combo_info["slots"])
                wildcard_slot_names = set(combo_info.get("wildcard_slots", []))
                if not combo_slot_names.issubset(valid_slot_names):
                    load_errors.append(
                        f"Intent does not support slot(s) used in slot combination: {error_info}, "
                        f"slots={combo_slot_names - valid_slot_names}"
                    )

                if not wildcard_slot_names.issubset(valid_slot_names):
                    load_errors.append(
                        f"Intent does not support wildcard slot(s) used in slot combination: {error_info}, "
                        f"slots={wildcard_slot_names - valid_slot_names}"
                    )

                if (
                    ("name" in combo_slot_names)
                    and ("name_domains" not in combo_info)
                    and ("name" not in wildcard_slot_names)
                ):
                    load_errors.append(
                        f"name_domains must be provided when name slot is used: {error_info}"
                    )

                # name_domains restricts "name" slot
                # inferred_domain is inferred by words used in the sentence
                if ("name_domains" in combo_info) and ("inferred_domain" in combo_info):
                    load_errors.append(
                        f"Cannot have both name_domains and inferred_domain: {error_info}"
                    )

    if (intent_schemas is None) or load_errors:
        print("File intents.yaml has invalid format:")
        for error in load_errors:
            print(f" - {error}")
        return 1

    # languages.yaml
    language_infos = _load_yaml_file(
        load_errors, None, LANGUAGES_FILE, LANGUAGES_SCHEMA
    )
    # If no load errors, validate some info.
    if language_infos:
        languages_without_files = set(LANGUAGES) - set(language_infos)
        if languages_without_files:
            load_errors.append(
                f"Contains language without files: {', '.join(sorted(languages_without_files))}"
            )
        if sorted(language_infos) != list(language_infos):
            load_errors.append("Languages should be sorted alphabetically")

    if (language_infos is None) or load_errors:
        print("File languages.yaml has invalid format:")
        for error in load_errors:
            print(f" - {error}")
        return 1

    # shared lists
    for list_path in LIST_DIR.glob("*.yaml"):
        list_name = list_path.stem
        list_info = _load_yaml_file(
            load_errors, None, list_path, SHARED_LISTS_SCHEMA(list_name)
        )

        if (list_info is None) or load_errors:
            print(f"File {list_path} has invalid format:")
            for error in load_errors:
                print(f" - {error}")
            return 1

    errors: dict[str, list[str]] = {}
    warnings: dict[str, list[str]] = {}

    for language in languages:
        errors[language] = []
        warnings[language] = []
        validate_language(
            language_infos.get(language),
            intent_schemas,
            language,
            errors[language],
            warnings[language],
        )
        validate_slot_combinations(
            intent_schemas, language, errors[language], warnings[language]
        )
        validate_lists(language, errors[language])
        validate_expansion_rules(language, errors[language])
        # Remove language if no errors
        if not errors[language]:
            errors.pop(language)

        if not warnings[language]:
            warnings.pop(language)

    if errors:
        print("Validation failed")
        print()

        for language, language_errors in errors.items():
            print(f"Language: {language}")
            for error in language_errors:
                print(f"[ERROR] {error}")
            print()
        return 1

    if warnings:
        for language, language_warnings in warnings.items():
            print(f"Language: {language}")
            for warning in language_warnings:
                print(f"[WARN] {warning}")
            print()

    print("All good!")
    return 0


def _load_yaml_file(
    errors: list, language: str | None, file_path: Path, schema: vol.Schema
) -> dict | None:
    """Load a YAML file."""
    path = str(file_path.relative_to(ROOT))
    try:
        content = yaml.safe_load(file_path.read_text(encoding="utf8"))
    except yaml.YAMLError as err:
        errors.append(f"{path}: invalid YAML: {err}")
        return None

    try:
        validate_with_humanized_errors(content, schema)
    except vol.Error as err:
        errors.append(f"{path}: invalid format: {err}")
        return None

    if language is not None and content["language"] != language:
        errors.append(f"{path}: references incorrect language {content['language']}")
        return None

    return content


def validate_language(
    language_info: dict | None,
    intent_schemas: dict,
    language: str,
    errors: list[str],
    warnings: list[str],
):
    sentence_dir: Path = SENTENCE_DIR / language
    test_dir: Path = TESTS_DIR / language
    response_dir: Path = RESPONSE_DIR / language

    if language_info is None:
        errors.append("Language not defined in languages.yaml")

    sentence_files = {}

    # intent -> {response}
    used_response_keys: dict[str, set[str]] = defaultdict(set)

    # intent -> sentence count
    num_intent_sentences: Counter[str] = Counter()

    for sentence_file in sentence_dir.glob("*.yaml"):
        path = str(sentence_file.relative_to(ROOT))

        if sentence_file.name == "_common.yaml":
            schema = SENTENCE_COMMON_SCHEMA
        else:
            schema = SENTENCE_SCHEMA

        content = _load_yaml_file(errors, language, sentence_file, schema)

        if sentence_file.name == "_common.yaml":
            continue

        sentence_files[sentence_file.name] = content

        if content is None:
            continue

        _domain, intent = sentence_file.stem.rsplit("_", maxsplit=1)

        if intent not in intent_schemas:
            errors.append(f"{path}: Filename references unknown intent {intent}.yaml")
            continue

        # Gather response keys used in intents.
        # They will be validated against the response files below.
        for intent in content["intents"]:
            for intent_data in content["intents"][intent]["data"]:
                response_key = intent_data.get("response", "default")
                used_response_keys[intent].add(response_key)

                # Track count of sentences for this intent
                num_intent_sentences[intent] += len(intent_data["sentences"])

    if not test_dir.exists():
        errors.append(f"{test_dir.relative_to(ROOT)}: Missing tests directory")
        return

    for test_file in test_dir.glob("*.yaml"):
        path = str(test_file.relative_to(ROOT))

        if test_file.name == "_fixtures.yaml":
            schema = TESTS_FIXTURES
        elif test_file.name == "_test_failures.yaml":
            schema = TESTS_FAILURES
        else:
            schema = TESTS_SCHEMA

        content = _load_yaml_file(errors, language, test_file, schema)

        if content is None:
            continue

        if test_file.name == "_fixtures.yaml":
            area_ids = set(area["id"] for area in content.get("areas", []))
            for entity in content.get("entities", []):
                area = entity.get("area")
                if (area is not None) and (area not in area_ids):
                    errors.append(
                        f"{path}: Entity {entity['name']} references unknown area {entity['area']}"
                    )
            continue

        if test_file.name == "_test_failures.yaml":
            continue

        if test_file.name not in sentence_files:
            errors.append(f"{path}: has no matching sentence file")
            continue

        sentence_content = sentence_files.pop(test_file.name)
        _domain, intent = test_file.stem.rsplit("_", maxsplit=1)

        # Ensure test file has the correct intent
        has_correct_intent = True
        for test in content["tests"]:
            test_intent = test["intent"]["name"]
            if test_intent != intent:
                errors.append(
                    f"{path}: expected intent {intent} but found {test_intent}"
                )
                has_correct_intent = False
                break

        if not has_correct_intent:
            continue

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
                errors.append(
                    f"{path}: not all sentences have tests ({test_count}/{sentence_count})"
                )

        missing_response_checks = 0
        for test_data in content["tests"]:
            if "response" not in test_data:
                missing_response_checks += 1

        if missing_response_checks > 0:
            warnings.append(
                f"{path}: {missing_response_checks} test(s) missing response check"
            )

    if sentence_files:
        for sentence_file_without_tests in sentence_files:
            errors.append(f"{sentence_file_without_tests} has no tests")

    # Environment used to render response templates
    jinja2_env = get_jinja2_environment()

    for response_file in response_dir.iterdir():
        path = str(response_file.relative_to(ROOT))
        intent = response_file.stem

        if intent not in intent_schemas:
            errors.append(
                f"{path}: Filename references unknown intent {response_file.stem}"
            )
            continue

        content = _load_yaml_file(errors, language, response_file, RESPONSE_SCHEMA)

        if content is None:
            continue

        if num_intent_sentences[intent] < 1:
            # Skip response key validation if there are no sentences defined for the intent.
            # This avoids CI validate problems with adding the test language.
            continue

        used_intent_response_keys: set[str] = used_response_keys.get(intent, set())
        for intent_name, intent_responses in content["responses"]["intents"].items():
            if intent != intent_name:
                errors.append(
                    f"{path}: references incorrect intent {intent_name}. Only {intent} allowed"
                )
                continue

            possible_response_keys: set[str] = set()
            slots: dict[str, Any] = {
                slot_name: f"<{slot_name}>"
                for slot_name in intent_schemas[intent_name].get("slots", {})
            }

            # For timer intents
            slots["timers"] = []
            slots["canceled"] = 0

            # For date/time intents
            slots["date"] = datetime.now().date()
            slots["time"] = datetime.now().time()

            for response_key, response_template in intent_responses.items():
                possible_response_keys.add(response_key)
                if response_key not in used_intent_response_keys:
                    warnings.append(f"{path}: unused response {response_key}")

                if response_template:
                    try:
                        jinja2_env.from_string(response_template).render(
                            {
                                "state": {
                                    "name": "<name>",
                                    "state": 0,
                                    "domain": "<domain>",
                                    "state_with_unit": "",
                                    "attributes": {},
                                },
                                "slots": slots,
                                "query": {"matched": [], "unmatched": []},
                                "state_attr": lambda *args: None,
                            }
                        )
                    except jinja2.exceptions.TemplateError as err:
                        errors.append(
                            f"{path}: {err.args[0]} in response '{response_key}' (template='{response_template}')"
                        )

            missing_response_keys = used_intent_response_keys - possible_response_keys
            for response_key in missing_response_keys:
                errors.append(f"{path}: response not defined {response_key}")


def validate_slot_combinations(
    intent_schemas: dict, language: str, errors: list[str], warnings: list[str]
) -> None:
    """Validate the sentence and test YAML files for each slot combination."""
    if language not in SLOT_COMBO_VALIDATION_LANGUAGES:
        return

    sentence_dir = SENTENCE_DIR / language
    test_dir = TESTS_DIR / language
    available_list_names = HA_LIST_NAMES.union(
        list_path.stem
        for list_path in itertools.chain(
            LIST_DIR.glob("*.yaml"),  # shared lists
            (LIST_DIR / language).glob("*.yaml"),  # language-specific lists
        )
    )
    available_rule_names = set(
        rule_path.stem for rule_path in (RULE_DIR / language).glob("*.yaml")
    )

    for intent_name in intent_schemas:
        intent_dir = sentence_dir / intent_name
        test_intent_dir = test_dir / intent_name

        available_response_names: set[str] = set()
        responses_path = RESPONSE_DIR / language / f"{intent_name}.yaml"
        if responses_path.exists():
            with open(responses_path, "r", encoding="utf-8") as responses_file:
                responses_dict = yaml.safe_load(responses_file)
                available_response_names.update(
                    responses_dict["responses"]["intents"][intent_name]
                )

        for combo_name, combo_info in intent_schemas[intent_name][
            "slot_combinations"
        ].items():
            error_info = f"intent_name={intent_name}, combo_name={combo_name}"
            combo_importance = combo_info["importance"]

            combo_sentence_path = intent_dir / f"{combo_name}.yaml"
            if not combo_sentence_path.exists():
                if combo_importance == "required":
                    errors.append(
                        f"Missing sentences for required slot combination: {error_info}, "
                        f"file={combo_sentence_path}"
                    )
                elif combo_importance == "usable":
                    warnings.append(
                        f"Missing sentences for usable slot combination: {error_info}, "
                        f"file={combo_sentence_path}"
                    )

                continue

            available_slot_names = set(combo_info.get("slots", []))
            if "inferred_domain" in combo_info:
                available_slot_names.discard("domain")

            # validate sentences
            _load_yaml_file(
                errors,
                language,
                combo_sentence_path,
                SLOT_COMBO_SENTENCE_SCHEMA(
                    language,
                    combo_name,
                    available_list_names,
                    available_slot_names,
                    available_rule_names,
                    available_response_names,
                ),
            )

            # validate tests
            combo_test_path = test_intent_dir / f"{combo_name}.yaml"
            if not combo_test_path.exists():
                errors.append(
                    f"Missing test file for slot combination: {error_info}, "
                    f"file={combo_test_path}"
                )
                continue

            _load_yaml_file(
                errors,
                language,
                combo_test_path,
                SLOT_COMBO_TEST_SCHEMA(language, available_slot_names),
            )


def validate_lists(language: str, errors: list[str]) -> None:
    lists_dir: Path = LIST_DIR / language
    for list_path in lists_dir.glob("*.yaml"):
        list_name = list_path.stem
        _load_yaml_file(
            errors, language, list_path, LANGUAGE_LISTS_SCHEMA(language, list_name)
        )


def validate_expansion_rules(language: str, errors: list[str]) -> None:
    rules_dir: Path = RULE_DIR / language
    for rule_path in rules_dir.glob("*.yaml"):
        rule_name = rule_path.stem
        _load_yaml_file(
            errors, language, rule_path, EXPANSION_RULES_SCHEMA(language, rule_name)
        )


# -----------------------------------------------------------------------------


def no_alternative_list_references(sentence: str):
    """Validator that doesn't allow for {list} references in (an|alternative) or [an optional]."""

    def visitor(e: Expression, arg: Any):
        if isinstance(e, Alternative):
            return True

        in_alternative: bool = arg

        if isinstance(e, ListReference) and in_alternative:
            list_ref: ListReference = e
            raise vol.Invalid(
                f"List references not allow in alternatives (a|b) or optionals [c] ({{{list_ref.list_name}}})"
            )

        return in_alternative

    _visit_expression(parse_sentence(sentence).expression, visitor, False)
    return sentence


def no_list_or_rule_references(sentence: str):
    """Validator that doesn't allow for {list} or <rule> references in a sentence template."""

    def visitor(e: Expression, arg: Any):
        if isinstance(e, ListReference):
            list_ref: ListReference = e
            raise vol.Invalid(
                f"List reference not allow in expansion rules: {{{list_ref.list_name}}}"
            )

        if isinstance(e, RuleReference):
            rule_ref: RuleReference = e
            raise vol.Invalid(
                f"Rule reference not allowed in expansion rules: <{rule_ref.rule_name}>"
            )

    _visit_expression(parse_sentence(sentence).expression, visitor, None)
    return sentence


def non_empty_string(value: Any):
    if not isinstance(value, str):
        raise vol.Invalid(f"Not a string: {value}")

    if not value.strip():
        raise vol.Invalid("String cannot be empty")

    return value


def not_optional(sentence: str):
    """Validator that ensures a sentence is not completely optional."""

    top_expression = parse_sentence(sentence).expression
    if isinstance(top_expression, Alternative):
        alt: Alternative = top_expression
        if alt.is_optional:
            raise vol.Invalid("Expansion rule must have some required text")

    return sentence


def allowed_list_names(list_names: set[str]):
    """Validator that ensures list reference names are valid."""

    def validator(sentence: str):
        def visitor(e: Expression, arg: Any):
            if isinstance(e, ListReference):
                list_ref: ListReference = e
                if list_ref.list_name not in list_names:
                    raise vol.Invalid(
                        "List is not defined for language: "
                        f"list_name=<{list_ref.list_name}>, "
                        f"list_names={list_names}"
                    )

        _visit_expression(parse_sentence(sentence).expression, visitor, None)
        return sentence

    return validator


def required_slots_names(slot_names: set[str]):
    """Validator that ensures required slot names are present."""

    def validator(sentence: str):

        def visitor(e: Expression, arg: Any):
            used_slot_names: set[str] = arg

            if isinstance(e, ListReference):
                list_ref: ListReference = e
                used_slot_names.add(list_ref.slot_name)

            return used_slot_names

        used_slot_names: set[str] = set()
        _visit_expression(parse_sentence(sentence).expression, visitor, used_slot_names)

        missing_slots = slot_names - used_slot_names
        if missing_slots:
            raise vol.Invalid(f"Missing required slots in sentence: {missing_slots}")

        extra_slots = used_slot_names - slot_names
        if extra_slots:
            raise vol.Invalid(f"Extra slots in sentence: {extra_slots}")

        if sentence == "(light up|illuminate) [<the>]":
            print(sentence, slot_names, used_slot_names)

        return sentence

    return validator


def allowed_rule_names(rule_names: set[str]):
    """Validator that ensures rule reference names are valid."""

    def validator(sentence: str):
        def visitor(e: Expression, arg: Any):
            if isinstance(e, RuleReference):
                rule_ref: RuleReference = e
                if rule_ref.rule_name not in rule_names:
                    raise vol.Invalid(
                        f"Rule is not defined for language: <{rule_ref.rule_name}>"
                    )

        _visit_expression(parse_sentence(sentence).expression, visitor, None)
        return sentence

    return validator


def _visit_expression(e: Expression, visitor, visitor_arg: Any):
    result = visitor(e, visitor_arg)
    if isinstance(e, Group):
        grp: Group = e
        for item in grp.items:
            _visit_expression(item, visitor, result)
