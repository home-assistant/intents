import io

import pytest

from hassil import Intents, parse_sentence, recognize
from hassil.intents import TextSlotList

TEST_YAML = """
language: "en"
intents:
  TurnOn:
    category: "action"
    data:
      - sentences:
        - "turn on [all] [the] lights in <area>"
        #- "turn [all] <area> lights on"
        slots:
          domain: "light"
          name: "all"
  #SetBrightness:
  #  category: "action"
  #  data:
  #    - sentences:
  #      - "set brightness in <area> to <brightness>"
  #      - "set brightness to <brightness> to <area>"
  #      slots:
  #        domain: "light"
  #        name: "all"
expansion_rules:
  area: "[the] {area}"
  brightness: "{brightness_pct} [percent]"
lists:
  brightness_pct:
    range:
      type: percentage
      from: 0
      to: 100
skip_words:
  - "please"
"""


@pytest.fixture
def intents():
    with io.StringIO(TEST_YAML) as test_file:
        return Intents.from_yaml(test_file)


@pytest.fixture
def slot_lists():
    return {
        "area": TextSlotList.from_tuples(
            [("kitchen", "area1"), ("living room", "area2")]
        )
    }


def test_1(intents, slot_lists):
    result = recognize(
        "turn on the lights in the kitchen, please", intents, slot_lists=slot_lists
    )
    assert result is not None
    assert result.intent.name == "TurnOn"

    area = result.entities["area"]
    assert area.name == "area"
    assert area.value == "area1"
    assert area.words == ["kitchen"]
    assert area.words_raw == ["kitchen,"]
    assert area.word_start_index == 6
    assert area.word_stop_index == 7
