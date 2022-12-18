from hassil import is_match, parse_sentence
from hassil.intents import TextSlotList


def test_no_match():
    sentence = parse_sentence("turn on the lights")
    assert is_match("turn on the lights", sentence)
    assert not is_match("turn off the lights", sentence)
    assert not is_match("don't turn on the lights", sentence)


def test_punctuation():
    sentence = parse_sentence("turn on the lights")
    assert is_match("turn on the lights.", sentence)
    assert is_match("turn on the lights!", sentence)


def test_whitespace():
    sentence = parse_sentence("turn on the lights")
    assert is_match("  turn      on the     lights", sentence)


def test_skip_nonword():
    sentence = parse_sentence("turn on the lights")
    assert is_match("turn ! on @ the # lights $", sentence)


def test_skip_words():
    sentence = parse_sentence("turn on [the] lights")
    skip_words = {"please", "could", "you", "my"}
    assert is_match(
        "could you please turn on my lights?", sentence, skip_words=skip_words
    )
    assert is_match("turn on the lights, please", sentence, skip_words=skip_words)


def test_optional():
    sentence = parse_sentence("turn on [the] lights in [the] kitchen")
    assert is_match("turn on the lights in the kitchen", sentence)
    assert is_match("turn on lights in kitchen", sentence)


def test_optional_plural():
    sentence = parse_sentence("turn on the light[s]")
    assert is_match("turn on the light", sentence)
    assert is_match("turn on the lights", sentence)


def test_group_plural():
    sentence = parse_sentence("give me the penn(y | ies)")
    assert is_match("give me the penny", sentence)
    assert is_match("give me the pennies", sentence)


def test_list():
    sentence = parse_sentence("turn off {area}")
    areas = TextSlotList.from_strings(["kitchen", "living room"])
    assert is_match("turn off kitchen", sentence, slot_lists={"area": areas})
    assert is_match("turn off living room", sentence, slot_lists={"area": areas})


def test_list_prefix_suffix():
    sentence = parse_sentence("turn off abc-{area}-123")
    areas = TextSlotList.from_strings(["kitchen", "living room"])
    assert is_match("turn off abc-kitchen-123", sentence, slot_lists={"area": areas})
    assert is_match(
        "turn off abc-living room-123", sentence, slot_lists={"area": areas}
    )


def test_rule():
    sentence = parse_sentence("turn off <area>")
    assert is_match(
        "turn off kitchen",
        sentence,
        expansion_rules={"area": parse_sentence("[the] kitchen")},
    )


def test_rule_prefix_suffix():
    sentence = parse_sentence("turn off abc-<area>-123")
    assert is_match(
        "turn off abc-kitchen-123",
        sentence,
        expansion_rules={"area": parse_sentence("[the] kitchen")},
    )
