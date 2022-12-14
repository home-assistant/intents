import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

from . import Intents, recognize
from .intents import TextSlotList
from .util import merge_dict

_LOGGER = logging.getLogger("hassil")
_DIR = Path(__file__).parent
_SENTENCES_DIR = _DIR.parent.parent / "sentences"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--language", default="en")
    parser.add_argument(
        "--areas",
        nargs="+",
        help="Area names",
        default=["kitchen", "bedroom", "living room"],
    )
    parser.add_argument("--names", nargs="+", default=[], help="Device/entity names")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    slot_lists = {
        "area": TextSlotList.from_strings(args.areas),
        "name": TextSlotList.from_strings(args.names),
    }

    lang_dir = _SENTENCES_DIR / args.language
    input_dict = {}
    for yaml_path in lang_dir.glob("*.yaml"):
        _LOGGER.debug("Loading file: %s", yaml_path)
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(input_dict, yaml.safe_load(yaml_file))

    assert input_dict, "No intent YAML files loaded"
    intents = Intents.from_dict(input_dict)

    if os.isatty(sys.stdout.fileno()):
        print("Reading sentences from stdin...", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            result = recognize(line, intents, slot_lists=slot_lists)
            if result is not None:
                print(
                    {
                        "intent": result.intent.name,
                        **{e.name: e.value for e in result.entities_list},
                    }
                )
            else:
                print("<no match>")
        except Exception:
            _LOGGER.exception(line)


if __name__ == "__main__":
    main()
