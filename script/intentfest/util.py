"""Translation utils."""
import argparse


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Home Assistant Translations")
    parser.add_argument(
        "action",
        type=str,
        choices=["add_language"],
    )
    parser.add_argument("--debug", action="store_true", help="Enable log output")
    return parser
