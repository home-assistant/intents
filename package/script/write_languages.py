"""
Generates a Python file with available domains/languages.

This is automatically run by script/package after the data files are generated.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_dir", help="Path to directory with <domain>/<language>.json files"
    )
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    domains_and_languages: Dict[str, List[str]] = defaultdict(list)

    # data/<domain>/<language>.json
    for domain_dir in sorted(data_dir.iterdir()):
        if not domain_dir.is_dir():
            continue

        domains_and_languages[domain_dir.name] = sorted(
            (language_file.stem for language_file in domain_dir.glob("*.json"))
        )

    print("DOMAINS_AND_LANGUAGES =", json.dumps(domains_and_languages))


if __name__ == "__main__":
    main()
