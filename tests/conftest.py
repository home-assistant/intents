"""Test configuration and fixtures."""
from __future__ import annotations

import pytest
import yaml
from hassil import Intents
from hassil.util import merge_dict

from . import INTENTS_FILE, LANGUAGES, load_sentences


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
def intent_schemas():
    """Loads the base intents file"""
    with open(INTENTS_FILE, "r", encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


@pytest.fixture(name="language_sentences_yaml", scope="session")
def language_sentences_yaml_fixture(language: str):
    """Loads the language sentences."""
    return load_sentences(language)


@pytest.fixture(scope="session")
def language_sentences(language_sentences_yaml: dict):
    """Parse language sentences."""
    merged: dict = {}
    for intents_dict in language_sentences_yaml.values():
        merge_dict(merged, intents_dict)

    return Intents.from_dict(merged)
