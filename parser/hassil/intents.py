from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, IO, Optional, Union

from dataclasses_json import config, dataclass_json, DataClassJsonMixin
from yaml import safe_load

from .expression import Sentence
from .parse import parse_sentences


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
    category: IntentCategory = IntentCategory.ACTION
    data: List[IntentData] = field(default_factory=list)


class SlotValue(ABC):
    pass


@dataclass_json
@dataclass
class TextSlotValue(SlotValue):
    text_in: str = field(metadata=config(field_name="in"))
    text_out: str = field(metadata=config(field_name="out"))


class RangeType(str, Enum):
    NUMBER = "number"
    PERCENTAGE = "percentage"
    DEGREES = "degrees"


@dataclass_json
@dataclass
class RangeSlotValue(SlotValue):
    range_from: int = field(metadata=config(field_name="from"))
    range_to: int = field(metadata=config(field_name="to"))
    range_step: int = field(default=1, metadata=config(field_name="step"))
    type: RangeType = RangeType.NUMBER


@dataclass
class Intents:
    language: str
    intents: Dict[str, Intent]
    # slot_lists: Dict[str, List[SlotValue]] = field(default_factory=dict)
    expansion_rules: Dict[str, Sentence] = field(default_factory=dict)
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
            expansion_rules={
                rule_name: parse_sentences([rule_body])[0]
                for rule_name, rule_body in input_dict.get(
                    "expansion_rules", {}
                ).items()
            },
        )
