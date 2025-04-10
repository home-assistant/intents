"""
Generates a JSON file with scores for each language.
These are based on the languages.yaml file in the intents repo.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Set

import yaml

_LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Writes language scores JSON to stdout."""
    logging.basicConfig(level=logging.INFO)
    script_dir = Path(__file__).parent
    intents_dir = script_dir.parent

    language_scores = {}

    with open(intents_dir / "languages.yaml", "r", encoding="utf-8") as languages_file:
        languages = yaml.safe_load(languages_file)

    with open(intents_dir / "intents.yaml", "r", encoding="utf-8") as intents_file:
        intents = yaml.safe_load(intents_file)

    required_intents: Set[str] = set()
    usable_intents: Set[str] = set()
    complete_intents: Set[str] = set()

    for intent_name, intent_info in intents.items():
        if not intent_info.get("supported"):
            # Skip intents that are not supported in Home Assistant
            continue

        importance = intent_info.get("importance")
        if importance == "required":
            required_intents.add(intent_name)
        elif importance == "usable":
            usable_intents.add(intent_name)
        elif importance == "complete":
            complete_intents.add(intent_name)

    for lang_key, lang_info in languages.items():
        if "-" in lang_key:
            # de-CH -> de
            lang_family = lang_key.split("-", maxsplit=1)[0]
        else:
            lang_family = lang_key

        lang_support = lang_info.get("support")
        if not lang_support:
            _LOGGER.warning("Missing support info for language: %s", lang_key)
            continue

        supported_intents: Set[str] = set()
        sentences_dir = intents_dir / "sentences" / lang_key

        for sentence_yaml_path in sentences_dir.glob("*.yaml"):
            with open(sentence_yaml_path, "r", encoding="utf-8") as sentences_yaml_file:
                sentences_yaml = yaml.safe_load(sentences_yaml_file)
                for lang_intent_name, lang_intent_info in sentences_yaml.get(
                    "intents", {}
                ).items():
                    if lang_intent_name in supported_intents:
                        # Already supported
                        continue

                    for lang_intent_data in lang_intent_info.get("data", []):
                        if len(lang_intent_data.get("sentences", [])) > 0:
                            supported_intents.add(lang_intent_name)
                            break

        has_required_intents = required_intents.issubset(supported_intents)
        has_usable_intents = usable_intents.issubset(supported_intents)
        has_complete_intents = complete_intents.issubset(supported_intents)

        for region, region_support in lang_support.items():
            locale = f"{lang_family}-{region}"
            stt = region_support.get("speech-to-text", {})
            tts = region_support.get("text-to-speech", {})

            cloud_score = 0
            focused_local_score = 0
            full_local_score = 0

            if stt.get("cloud") and tts.get("cloud"):
                if has_complete_intents:
                    cloud_score = 3
                elif has_usable_intents:
                    cloud_score = 2
                elif has_required_intents:
                    cloud_score = 1

            if stt.get("speech-to-phrase") and tts.get("piper"):
                if has_complete_intents:
                    focused_local_score = 2  # cannot be perfect
                elif has_usable_intents:
                    focused_local_score = 2
                elif has_required_intents:
                    focused_local_score = 1

            if stt.get("whisper") and tts.get("piper"):
                if has_complete_intents:
                    full_local_score = 3
                elif has_usable_intents:
                    full_local_score = 2
                elif has_required_intents:
                    full_local_score = 1

            language_scores[locale] = {
                "cloud": cloud_score,
                "focused_local": focused_local_score,
                "full_local": full_local_score,
            }

    json.dump(language_scores, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
