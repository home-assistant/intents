from hassil.generate import generate_expression
from hassil.intents import RangeSlotList, TextSlotList
from hassil.parse import parse_sentence


def test_text_chunk():
    assert set(generate_expression(parse_sentence("this is a test"))) == {
        "this is a test"
    }


def test_group():
    assert set(generate_expression(parse_sentence("this (is a) test"))) == {
        "this is a test"
    }


def test_optional():
    assert set(generate_expression(parse_sentence("this is [a] test"))) == {
        "this is test",
        "this is a test",
    }


def test_alternative():
    assert set(generate_expression(parse_sentence("this is (the | a) test"))) == {
        "this is a test",
        "this is the test",
    }


def test_list():
    sentence = parse_sentence("turn off {area}")
    areas = TextSlotList.from_strings(["kitchen", "living room"])
    assert set(generate_expression(sentence, slot_lists={"area": areas})) == {
        "turn off kitchen",
        "turn off living room",
    }


def test_list_range():
    sentence = parse_sentence("run test {num}")
    num_list = RangeSlotList(1, 3)
    assert set(generate_expression(sentence, slot_lists={"num": num_list})) == {
        "run test 1",
        "run test 2",
        "run test 3",
    }


def test_rule():
    sentence = parse_sentence("turn off <area>")
    assert set(
        generate_expression(
            sentence,
            expansion_rules={"area": parse_sentence("[the] kitchen")},
        )
    ) == {"turn off kitchen", "turn off the kitchen"}
