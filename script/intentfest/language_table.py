"""Script to print Markdown language table."""

import yaml

from .const import LANGUAGES_FILE


def run() -> int:
    print("|Code|Language|Leaders|")
    print("|--|--|--|")

    languages = yaml.safe_load(LANGUAGES_FILE.read_text())
    for code in sorted(languages):
        info = languages[code]
        name = info["nativeName"]
        leaders = info.get("leaders")

        if leaders:
            leaders_str = ", ".join(f"@{leader}" for leader in leaders)
        else:
            leaders_str = "(position open)"

        print("|", f"`{code}`", "|", name, "|", leaders_str, "|")

    return 0
