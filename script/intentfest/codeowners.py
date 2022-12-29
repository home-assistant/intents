"""Generate codeowners."""
from __future__ import annotations

import argparse

import yaml

from .const import ROOT, LANGUAGES_FILE
from .util import get_base_arg_parser


CODEOWNERS_FILE = ROOT / "CODEOWNERS"


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--check",
        required=False,
        action="store_true",
        help="Check if the file is correct format instead of writing it.",
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    languages = yaml.safe_load(LANGUAGES_FILE.read_text())

    parts = []

    for language, info in languages.items():
        if not info.get("leaders"):
            continue

        leaders = " ".join(f"@{leader}" for leader in sorted(info["leaders"]))
        parts.extend(
            [
                f"sentences/{language}/ {leaders}",
                f"responses/{language}/ {leaders}",
                f"tests/{language}/ {leaders}",
                "",
            ]
        )

    output = "\n".join(parts)

    if args.check:
        if CODEOWNERS_FILE.read_text() != output:
            print("Codeowners file is not up to date")
            print("Update with: python3 -m script.intentfest codeowners")
            return 1
        return 0

    CODEOWNERS_FILE.write_text(output)
    return 0
