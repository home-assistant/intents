from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import IO, Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from dataclasses_json import DataClassJsonMixin, config, dataclass_json
from yaml import safe_load

from .expression import Sentence
from .parse import parse_sentence, parse_sentences


class IntentCategory(str, Enum):
    ACTION = "action"
    QUERY = "query"


class ResponseType(str, Enum):
    SUCCESS = "success"
    NO_INTENT = "no_intent"
    NO_AREA = "no_area"
    NO_DOMAIN = "no_domain"
    NO_DEVICE_CLASS = "no_device_class"
    NO_ENTITY = "no_entity"
    HANDLE_ERROR = "handle_error"


@dataclass
class IntentData:
    sentences: List[Sentence]
    slots: Dict[str, Any] = field(default_factory=dict)
    # requires_context: List[str] = field(default_factory=list)
    # response: Optional[str] = None


@dataclass_json
@dataclass
class Intent:
    name: str
    category: IntentCategory = IntentCategory.ACTION
    data: List[IntentData] = field(default_factory=list)


class SlotList(ABC):
    pass


class RangeType(str, Enum):
    NUMBER = "number"
    PERCENTAGE = "percentage"
    TEMPERATURE = "temperature"


@dataclass
class RangeSlotList(SlotList):
    start: int
    stop: int
    step: int = 1
    type: RangeType = RangeType.NUMBER

    def __post_init__(self):
        assert self.start < self.stop, "start must be less than stop"
        assert self.step > 0, "step must be positive"


@dataclass_json
@dataclass
class TextSlotValue:
    text_in: Sentence
    value_out: Any


@dataclass
class TextSlotList(SlotList):
    values: List[TextSlotValue]

    @staticmethod
    def from_strings(strings: Iterable[str]) -> "TextSlotList":
        return TextSlotList(
            values=[
                TextSlotValue(text_in=parse_sentence(text), value_out=text)
                for text in strings
            ],
        )

    @staticmethod
    def from_tuples(tuples: Iterable[Tuple[str, Any]]) -> "TextSlotList":
        return TextSlotList(
            values=[
                TextSlotValue(text_in=parse_sentence(text), value_out=value)
                for text, value in tuples
            ],
        )


@dataclass
class Intents:
    language: str
    intents: Dict[str, Intent]
    slot_lists: Dict[str, SlotList] = field(default_factory=dict)
    expansion_rules: Dict[str, Sentence] = field(default_factory=dict)
    skip_words: Set[str] = field(default_factory=set)
    # responses: Dict[ResponseType, Union[str, List[str]]] = field(default_factory=dict)

    @staticmethod
    def from_yaml(yaml_file: IO[str]) -> "Intents":
        return Intents.from_dict(safe_load(yaml_file))

    @staticmethod
    def from_dict(input_dict: Dict[str, Any]) -> "Intents":
        return Intents(
            language=input_dict["language"],
            intents={
                intent_name: Intent(
                    name=intent_name,
                    category=IntentCategory(intent_dict["category"]),
                    data=[
                        IntentData(
                            sentences=parse_sentences(data_dict["sentences"]),
                            slots=data_dict.get("slots", {}),
                        )
                        for data_dict in intent_dict["data"]
                    ],
                )
                for intent_name, intent_dict in input_dict["intents"].items()
            },
            slot_lists={
                list_name: _parse_list(list_dict)
                for list_name, list_dict in input_dict.get("lists", {}).items()
            },
            expansion_rules={
                rule_name: parse_sentences([rule_body])[0]
                for rule_name, rule_body in input_dict.get(
                    "expansion_rules", {}
                ).items()
            },
            skip_words=set(input_dict.get("skip_words", [])),
        )


def _parse_list(list_dict: Dict[str, Any]) -> SlotList:
    if "values" in list_dict:
        # Text
        text_values: List[TextSlotValue] = []
        for value in list_dict["values"]:
            if isinstance(value, str):
                # String value
                text_values.append(
                    TextSlotValue(text_in=parse_sentence(value), value_out=value)
                )
            else:
                # Object with "in" and "out"
                text_values.append(
                    TextSlotValue(
                        text_in=parse_sentence(value["in"]), value_out=value["out"]
                    )
                )

        return TextSlotList(text_values)

    if "range" in list_dict:
        # Range
        range_dict = list_dict["range"]
        return RangeSlotList(
            type=RangeType(range_dict.get("type", "number")),
            start=int(range_dict["from"]),
            stop=int(range_dict["to"]),
            step=int(range_dict.get("step", 1)),
        )

    raise ValueError(f"Unknown slot list type: {list_dict}")
