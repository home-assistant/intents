"""Test configuration and fixtures."""
import pytest
import yaml

from . import (
    INTENTS_FILE,
    load_intents,
    load_tests,
)


@pytest.fixture(scope="session")
def intent_schemas():
    """Loads the base intents file"""
    with open(INTENTS_FILE, "r", encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


@pytest.fixture(scope="session")
def language_intents(language: str):
    """Loads the base intents file"""
    return load_intents(language)


@pytest.fixture(scope="session")
def language_tests(language: str):
    """Loads the base intents file"""
    return load_tests(language)
