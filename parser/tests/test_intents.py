from hassil import parse_sentence, is_match


def test_no_match():
    sentence = parse_sentence("turn on the lights")
    assert is_match("turn on the lights", sentence)
    assert not is_match("turn off the lights", sentence)
    assert not is_match("don't turn on the lights", sentence)

def test_punctuation():
    sentence = parse_sentence("turn on the lights")
    assert is_match("turn on the lights.", sentence)
    assert is_match("turn on the lights!", sentence)


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


def test_list():
    sentence = parse_sentence("turn off {area}")
    areas = [parse_sentence(area_name) for area_name in ["kitchen", "living room"]]
    assert is_match("turn off kitchen", sentence, slot_lists={"area": areas})
    assert is_match("turn off living room", sentence, slot_lists={"area": areas})


def test_rule():
    sentence = parse_sentence("turn off <area>")
    assert is_match(
        "turn off kitchen",
        sentence,
        slot_lists={"area": [parse_sentence("kitchen")]},
        expansion_rules={"area": parse_sentence("[the] {area}")},
    )


def test_number():
    sentence = parse_sentence("execute order 66")
    assert is_match("execute order 66.", sentence)


def test_number_range():
    sentence = parse_sentence("set brightness to {brightness_pct}")
    slot_lists = {"brightness_pct": [parse_sentence("1..100 [percent]")]}
    assert is_match("set brightness to 50%", sentence, slot_lists=slot_lists)
    assert is_match("set brightness to 50 percent", sentence, slot_lists=slot_lists)
