"""Test configuration and fixtures."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
import yaml
from hassil import Intents, merge_dict

from . import INTENTS_FILE, LANGUAGES, RESPONSES_DIR, load_sentences


def pytest_addoption(parser):
    parser.addoption("--language", action="store", default=None)


def pytest_generate_tests(metafunc):
    # if the argument is specified in the list of test "fixturenames".
    if "language" in metafunc.fixturenames:
        option_value = metafunc.config.option.language
        if option_value is None:
            option_value = LANGUAGES
        else:
            option_value = option_value.split(",")
        metafunc.parametrize("language", option_value, scope="session")


@pytest.fixture(scope="session")
def intent_schemas() -> dict[str, Any]:
    """Loads the base intents file"""
    with open(INTENTS_FILE, "r", encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


@pytest.fixture(name="language_sentences_yaml", scope="session")
def language_sentences_yaml_fixture(language: str) -> dict[str, Any]:
    """Loads the language sentences."""
    return load_sentences(language)


@pytest.fixture(name="language_sentences_common", scope="session")
def language_sentences_common_fixture(
    language: str,
    language_sentences_yaml: dict[str, Any],
) -> Intents:
    """Loads the common language intents."""
    language_sentences_yaml["_common.yaml"].setdefault("intents", {})
    return Intents.from_dict(language_sentences_yaml["_common.yaml"])


@pytest.fixture(scope="session")
def language_sentences(
    language_sentences_yaml: dict[str, Any],
    language_sentences_common: Intents,
) -> Intents:
    """Parse language sentences."""
    merged: dict = {}
    for file_name, intents_dict in language_sentences_yaml.items():
        if file_name == "_common.yaml":
            continue
        merge_dict(merged, intents_dict)

    intents = Intents.from_dict(merged)

    return dataclasses.replace(language_sentences_common, intents=intents.intents)


@pytest.fixture(scope="session")
def language_responses(language: str) -> dict[str, Any]:
    """Load intent responses for a language."""
    merged_responses: dict = {}
    for response_file in (RESPONSES_DIR / language).iterdir():
        merge_dict(merged_responses, yaml.safe_load(response_file.read_text()))
    return merged_responses.get("responses", {}).get("intents", {})
