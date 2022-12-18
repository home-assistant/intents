import io

import pytest

from hassil import Intents, recognize
from hassil.intents import TextSlotList

TEST_YAML = """
language: "en"
intents:
  TurnOnTV:
    data:
      - sentences:
        - "turn on [the] TV in <area>"
        - "turn on <area> TV"
        slots:
          domain: "media_player"
          name: "roku"
  SetBrightness:
    data:
      - sentences:
        - "set [the] brightness in <area> to <brightness>"
        slots:
          domain: "light"
          name: "all"
  GetTemperature:
    data:
      - sentences:
        - "<what_is> [the] temperature in <area>"
        slots:
          domain: "climate"
expansion_rules:
  area: "[the] {area}"
  brightness: "{brightness_pct} [percent]"
  what_is: "(what's | whats | what is)"
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


# pylint: disable=redefined-outer-name
def test_turn_on(intents, slot_lists):
    result = recognize("turn on kitchen TV, please", intents, slot_lists=slot_lists)
    assert result is not None
    assert result.intent.name == "TurnOnTV"

    area = result.entities["area"]
    assert area.name == "area"
    assert area.value == "area.kitchen"

    # From YAML
    assert result.entities["domain"].value == "media_player"
    assert result.entities["name"].value == "roku"


# pylint: disable=redefined-outer-name
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


# pylint: disable=redefined-outer-name
def test_temperature(intents, slot_lists):
    result = recognize(
        "what is the temperature in the living room?", intents, slot_lists=slot_lists
    )
    assert result is not None
    assert result.intent.name == "GetTemperature"

    assert result.entities["area"].value == "area.living_room"

    # From YAML
    assert result.entities["domain"].value == "climate"
