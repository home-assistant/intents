"""Validate all intent files."""

import argparse

import yaml

from .const import INTENTS_FILE, LANGUAGES, SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser, require_sentence_domain_slot


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language", type=str, choices=LANGUAGES, help="The language to validate."
    )
    return parser.parse_args()


def run():
    args = get_arguments()

    if args.language is None:
        languages = LANGUAGES
    else:
        languages = [args.language]

    intent_schemas = yaml.safe_load(INTENTS_FILE.read_text())

    errors = {}

    for language in languages:
        errors[language] = []
        validate_language(intent_schemas, language, errors)
        # Remove language if no errors
        if not errors[language]:
            errors.pop(language)

    if errors:
        print("Validation failed:")
        for language, language_errors in errors.items():
            print(f"Language: {language}")
            for error in language_errors:
                print(f" - {error}")
        exit(1)

    print("All good!")


def validate_language(intent_schemas, language, errors):
    language_dir = SENTENCE_DIR / language
    test_dir = TESTS_DIR / language

    language_files = set()

    for language_file in language_dir.iterdir():
        language_files.add(language_file.name)

        if language_file.name == "_common.yaml":
            info = yaml.safe_load(language_file.read_text())
            if info["language"] != language:
                errors[language].append(
                    f"File {language_file.name} references incorrect language {info['language']}"
                )
            continue

        domain, intent = language_file.stem.split("_")

        if intent not in intent_schemas:
            errors[language].append(
                f"Filename {language_file.name} references unknown intent {intent}.yaml"
            )
            continue

        sentences = yaml.safe_load(language_file.read_text())
        if sentences["language"] != language:
            errors[language].append(
                f"File {language_file.name} references incorrect language {sentences['language']}"
            )

        for intent_name, intent_info in sentences["intents"].items():
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

        info = yaml.safe_load(test_file.read_text())
        if info["language"] != language:
            errors[language].append(
                f"Test {test_file.name} references incorrect language {info['language']}"
            )

    if language_files:
        for language_file in language_files:
            errors[language].append(f"{language_file} has no tests")
