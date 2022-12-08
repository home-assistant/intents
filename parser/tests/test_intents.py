import io

import pytest

from hassil.parse import parse_sentence
from hassil.recognize import is_match


def test_1():
    sentence = parse_sentence("turn on [the] lights in [the] kitchen")
    assert is_match("turn on the lights in the kitchen", sentence)
    assert is_match("turn on lights in kitchen", sentence)


def test_2():
    sentence = parse_sentence("turn off {area}")
    areas = [parse_sentence(area_name) for area_name in ["kitchen", "living room"]]
    assert is_match("turn off kitchen", sentence, slot_lists={"area": areas})
    assert is_match("turn off living room", sentence, slot_lists={"area": areas})


def test_3():
    sentence = parse_sentence("turn off <area>")
    assert is_match(
        "turn off kitchen",
        sentence,
        slot_lists={"area": [parse_sentence("kitchen")]},
        expansion_rules={"area": parse_sentence("[the] {area}")},
    )


# from hassil import Intents

# TEST_YAML = """
# language: "en"
# intents:
#   TurnOn:
#     category: "action"
#     data:
#       - sentences:
#         - "turn on lights in <area>"
#         - "turn <area> lights on"
#         slots:
#           domain: "light"
#           name: "all"
# expansion_rules:
#   area: "[the] {area}"
# """


# @pytest.fixture
# def intents():
#     with io.StringIO(TEST_YAML) as test_file:
#         return Intents.from_yaml(test_file)


# def test_1(intents):
#     assert False, intents
