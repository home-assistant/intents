"""Script to add a new language."""
import argparse

import yaml

from .const import RESPONSE_DIR, ROOT, SENTENCE_DIR, TESTS_DIR
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
        if require_sentence_domain_slot(intent, domain):
            sentence_info["slots"] = {
                "domain": domain,
                "name": "all",
            }

        (sentence_dir / english_filename.name).write_text(
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

    (sentence_dir / "_common.yaml").write_text(
        yaml.dump(
            {
                "language": language,
                "responses": {
                    "errors": {
                        "no_intent": [
                            {"template": "TODO Sorry, I couldn't understand that"}
                        ],
                        "no_area": [{"template": "TODO No area named {{ area }}"}],
                        "no_domain": [
                            {
                                "template": "TODO {{ area }} does not contain a {{ domain }}"
                            }
                        ],
                        "no_device_class": [
                            {
                                "template": "TODO {{ area }} does not contain a {{ device_class }}"
                            }
                        ],
                        "no_entity": [
                            {"template": "TODO No device or entity named {{ entity }}"}
                        ],
                        "handle_error": [
                            {
                                "template": "TODO An unexpected error occurred while handling the intent"
                            }
                        ],
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

    english_responses = RESPONSE_DIR / "en"

    for english_filename in english_responses.iterdir():
        intent = english_filename.stem

        (response_dir / english_filename.name).write_text(
            yaml.dump(
                {
                    "language": language,
                    "responses": {
                        "intents": {
                            intent: {
                                "success": [{"templates": []}],
                            },
                        },
                    },
                },
                sort_keys=False,
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
