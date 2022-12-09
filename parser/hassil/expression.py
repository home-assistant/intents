import re
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional

# 0..100, -100..100
NUMBER_RANGE_PATTERN = re.compile(r"^(-?[0-9]+)\.\.(-?[0-9]+),?(?P<step>[0-9]+)?$")
NUMBER_PATTERN = re.compile(r"^(-?[0-9]+)$")


def remove_escapes(text: str) -> str:
    """Remove backslash escape sequences"""
    return re.sub(r"\\(.)", r"\1", text)


def remove_quotes(text: str) -> str:
    """Remove double quotes"""
    if (len(text) > 1) and (text[0] == '"') and (text[-1] == '"'):
        text = text[1:-1]

    return text


@dataclass
class Expression(ABC):
    """Base class for expressions."""


@dataclass
class Word(Expression):
    """Single word/token."""

    # Text representation expression
    text: str = ""

    @property
    def is_empty(self) -> bool:
        """True if the word is empty"""
        return self.text == ""

    @staticmethod
    def empty() -> "Word":
        """Returns an empty word"""
        return Word()


class SequenceType(str, Enum):
    """Type of a sequence. Optionals are alternatives with an empty option."""

    # Sequence of expressions
    GROUP = "group"

    # Expressions where only one will be recognized
    ALTERNATIVE = "alternative"


@dataclass
class Sequence(Expression):
    """Ordered sequence of expressions. Supports groups, optionals, and alternatives."""

    # Items in the sequence
    items: List[Expression] = field(default_factory=list)

    # Group or alternative
    type: SequenceType = SequenceType.GROUP


@dataclass
class RuleReference(Expression):
    """Reference to an expansion rule by <name>."""

    # Name of referenced rule
    rule_name: str = ""


@dataclass
class ListReference(Expression):
    """Reference to a list by {name}."""

    list_name: str = ""


@dataclass
class Number(Expression):
    """Single number."""

    number: Optional[int] = None


@dataclass
class NumberRange(Expression):
    """Number range of the form N..M where N<M."""

    lower_bound: int
    upper_bound: int
    step: int = 1

    def __post_init__(self):
        assert (
            self.lower_bound < self.upper_bound
        ), "lower bound must be lower than upper bound"
        assert self.step > 0, "step must be positive"

    def __contains__(self, item):
        if self.step == 1:
            return self.lower_bound <= item <= self.upper_bound

        return item in range(self.lower_bound, self.upper_bound + 1, self.step)


@dataclass
class Sentence(Sequence):
    """Sequence representing a complete sentence template."""
