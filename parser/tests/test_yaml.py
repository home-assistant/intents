import io

import pytest

from hassil import Intents, recognize
from hassil.intents import TextSlotList

TEST_YAML = """
language: "en"
intents:
  TurnOnTV:
    category: "action"
    data:
      - sentences:
        - "turn on [the] TV in <area>"
        slots:
          domain: "media_player"
          name: "roku"
  SetBrightness:
    category: "action"
    data:
      - sentences:
        - "set [the] brightness in <area> to <brightness>"
        slots:
          domain: "light"
          name: "all"
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
            [("kitchen", "area.kitchen"), ("living room", "area.living_room")]
        )
    }


def test_turn_on(intents, slot_lists):
    result = recognize(
        "turn on the tv in the kitchen, please", intents, slot_lists=slot_lists
    )
    assert result is not None
    assert result.intent.name == "TurnOnTV"

    area = result.entities["area"]
    assert area.name == "area"
    assert area.value == "area.kitchen"
    assert area.words == ["kitchen"]
    assert area.words_raw == ["kitchen,"]
    assert area.word_start_index == 6
    assert area.word_stop_index == 7

    # From YAML
    assert result.entities["domain"].value == "media_player"
    assert result.entities["name"].value == "roku"


def test_brightness(intents, slot_lists):
    result = recognize(
        "set the brightness in the living room to 75%", intents, slot_lists=slot_lists
    )
    assert result is not None
    assert result.intent.name == "SetBrightness"

    assert result.entities["area"].value == "area.living_room"
    assert result.entities["brightness_pct"].value == 75

    # From YAML
    assert result.entities["domain"].value == "light"
    assert result.entities["name"].value == "all"
