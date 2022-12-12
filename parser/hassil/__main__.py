import argparse
import logging
import os
import sys

import yaml

from . import Intents, recognize
from .intents import TextSlotList
from .util import merge_dict

_LOGGER = logging.getLogger("hassil")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file", nargs="+")
    parser.add_argument("--areas", nargs="+", help="Area names")
    parser.add_argument("--names", nargs="+", help="Device/entity names")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    slot_lists = {}
    if args.areas:
        slot_lists["area"] = TextSlotList.from_strings(args.areas)

    if args.names:
        slot_lists["name"] = TextSlotList.from_strings(args.names)

    input_dict = {}
    for yaml_path in args.yaml_file:
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            merge_dict(input_dict, yaml.safe_load(yaml_file))

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
