"""Script to add a new language."""
import argparse

import yaml

from .const import SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser, require_sentence_domain_slot


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument("language", type=str, help="The language to add.")
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    language = args.language

    # Create language directory
    language_dir = SENTENCE_DIR / language
    tests_dir = TESTS_DIR / language
    try:
        language_dir.mkdir()
        tests_dir.mkdir()
    except FileExistsError:
        print(f"Language '{language}' already exists")
        return

    # Create sentence files based off English
    english_sentences = SENTENCE_DIR / "en"

    for english_filename in english_sentences.iterdir():
        if english_filename.name == "_common.yaml":
            continue

        domain, intent = english_filename.stem.split("_")

        sentence_info = {
            "sentences": [],
        }
        if require_sentence_domain_slot(intent, domain):
            sentence_info["slots"] = {
                "domain": domain,
                "name": "all",
            }

        (language_dir / english_filename.name).write_text(
            yaml.dump(
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
                sort_keys=False,
            )
        )

    (language_dir / "_common.yaml").write_text(
        yaml.dump(
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
            sort_keys=False,
        )
    )

    # Create tests files based off English
    english_tests = TESTS_DIR / "en"

    for english_filename in english_tests.iterdir():
        if english_filename.name == "_common.yaml":
            continue

        _domain, intent = english_filename.stem.split("_")

        (tests_dir / english_filename.name).write_text(
            yaml.dump(
                {
                    "language": language,
                    "tests": [
                        {
                            "sentences": [],
                            "intent": {
                                "name": intent,
                                "slots": {},
                            },
                        },
                    ],
                },
                sort_keys=False,
            )
        )

    (tests_dir / "_common.yaml").write_text(
        yaml.dump(
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
                        "domain": "light",
                    },
                    {
                        "name": "Kitchen Switch",
                        "id": "switch.kitchen",
                        "area": "kitchen",
                        "domain": "switch",
                    },
                    {
                        "name": "Ceiling Fan",
                        "id": "fan.ceiling",
                        "area": "living_room",
                        "domain": "fan",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    return 0
