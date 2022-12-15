"""Test configuration and fixtures."""
import pytest
import yaml

from . import INTENTS_FILE, LANGUAGES, load_intents, load_tests


def pytest_addoption(parser):
    parser.addoption("--language", action="store", default=None)


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.language
    if option_value is None:
        option_value = LANGUAGES
    else:
        option_value = option_value.split(",")
    if "language" in metafunc.fixturenames:
        metafunc.parametrize("language", option_value, scope="session")


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
