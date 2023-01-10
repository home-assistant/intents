"""Script to add a new language."""
import argparse
from functools import partial

import yaml

from .const import (
    INTENTS_FILE,
    LANGUAGES_FILE,
    RESPONSE_DIR,
    ROOT,
    SENTENCE_DIR,
    TESTS_DIR,
)
from .util import YamlDumper, get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "language",
        type=str,
        help="ISO 639 code of the language.",
    )
    parser.add_argument(
        "native_name",
        type=str,
        help="Name of the language in its own language.",
    )
    parser.add_argument(
        "--rtl",
        action="store_true",
        help="Specify if the language is right-to-left.",
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    language = args.language
    yaml_dump = partial(
        yaml.dump, sort_keys=False, allow_unicode=True, Dumper=YamlDumper
    )

    intent_schemas = yaml.safe_load(INTENTS_FILE.read_text())

    # Create language directory
    sentence_dir = SENTENCE_DIR / language
    tests_dir = TESTS_DIR / language
    response_dir = RESPONSE_DIR / language

    try:
        sentence_dir.mkdir()
        response_dir.mkdir()
        tests_dir.mkdir()
    except FileExistsError:
        print(f"Language '{language}' already exists")
        return 1

    # Create sentence files based off English
    english_sentences = SENTENCE_DIR / "en"

    for english_filename in english_sentences.iterdir():
        if english_filename.name == "_common.yaml":
            continue

        domain, intent = english_filename.stem.split("_")

        sentence_info: dict = {
            "sentences": [],
        }
        if domain != intent_schemas[intent]["domain"]:
            sentence_info["slots"] = {
                "domain": domain,
                "name": "all",
            }

        (sentence_dir / english_filename.name).write_text(
            yaml_dump(
                {
                    "language": language,
                    "intents": {
                        intent: {
                            "data": [
                                sentence_info,
                            ],
                        },
                    },
                },
            )
        )

    (sentence_dir / "_common.yaml").write_text(
        yaml_dump(
            {
                "language": language,
                "responses": {
                    "errors": {
                        "no_intent": "TODO Sorry, I couldn't understand that",
                        "no_area": "TODO No area named {{ area }}",
                        "no_domain": "TODO {{ area }} does not contain a {{ domain }}",
                        "no_device_class": "TODO {{ area }} does not contain a {{ device_class }}",
                        "no_entity": "TODO No device or entity named {{ entity }}",
                        "handle_error": "TODO An unexpected error occurred while handling the intent",
                    },
                },
                "lists": {},
                "expansion_rules": {},
                "skip_words": [],
            },
        )
    )

    # Create tests files based off English
    english_tests = TESTS_DIR / "en"

    for english_filename in english_tests.iterdir():
        if english_filename.name == "_fixtures.yaml":
            continue

        domain, intent = english_filename.stem.split("_")

        slots = {}

        if domain != intent_schemas[intent]["domain"]:
            slots = {"domain": domain, "name": "all"}

        (tests_dir / english_filename.name).write_text(
            yaml_dump(
                {
                    "language": language,
                    "tests": [
                        {
                            "sentences": [],
                            "intent": {
                                "name": intent,
                                "slots": slots,
                            },
                        },
                    ],
                },
            )
        )

    (tests_dir / "_fixtures.yaml").write_text(
        yaml_dump(
            {
                "language": language,
                "areas": [
                    {"name": "Kitchen", "id": "kitchen"},
                    {"name": "Living Room", "id": "living_room"},
                    {"name": "Bedroom", "id": "bedroom"},
                    {"name": "Garage", "id": "garage"},
                ],
                "entities": [
                    {
                        "name": "Bedroom Lamp",
                        "id": "light.bedroom_lamp",
                        "area": "bedroom",
                    },
                    {
                        "name": "Kitchen Switch",
                        "id": "switch.kitchen",
                        "area": "kitchen",
                    },
                    {
                        "name": "Ceiling Fan",
                        "id": "fan.ceiling",
                        "area": "living_room",
                    },
                ],
            },
        )
    )

    english_responses = RESPONSE_DIR / "en"

    for english_filename in english_responses.iterdir():
        intent = english_filename.stem

        (response_dir / english_filename.name).write_text(
            yaml_dump(
                {
                    "language": language,
                    "responses": {
                        "intents": {
                            intent: {
                                "success": [],
                            },
                        },
                    },
                },
            )
        )

    # Update languages.yaml
    languages = yaml.safe_load(LANGUAGES_FILE.read_text())
    languages[language] = {
        "nativeName": args.native_name,
    }
    if args.rtl:
        languages[language]["isRTL"] = True

    LANGUAGES_FILE.write_text(
        yaml_dump(
            # Sort the languages by code.
            dict(sorted(languages.items())),
        )
    )

    rel_sentence_dir = sentence_dir.relative_to(ROOT)
    rel_test_dir = tests_dir.relative_to(ROOT)

    print()
    print(f"Language '{language}' added!")
    print()
    print("See the README.md files in the sentences, responses and tests dir ")
    print("for the formats. Use the English files as examples.")
    print()
    print()
    print("New folders added:")
    print()
    print(f"{rel_sentence_dir} - Sentences")
    print(f"{response_dir.relative_to(ROOT)} - Responses")
    print(f"{rel_test_dir} - Tests")
    print()
    print()
    print("Limit your first contribution to:")
    print()
    print(
        f"{rel_sentence_dir / '_common.yaml'} - Update error strings and add skip words"
    )
    print()
    print(
        f"{rel_sentence_dir / 'homeassistant_HassTurnOn.yaml'} - Add some basic sentences"
    )
    print(
        f"{rel_sentence_dir / 'homeassistant_HassTurnOff.yaml'} - Add some basic sentences"
    )
    print()
    print(f"{rel_test_dir / 'homeassistant_HassTurnOn.yaml'} - Add test sentences")
    print(f"{rel_test_dir / 'homeassistant_HassTurnOff.yaml'} - Add test sentences")

    return 0
