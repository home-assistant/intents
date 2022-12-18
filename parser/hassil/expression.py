"""Classes for representing sentence templates."""
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


@dataclass
class Expression(ABC):
    """Base class for expressions."""


@dataclass
class TextChunk(Expression):
    """Contiguous chunk of text (with whitespace)."""

    # Text representation expression
    text: str = ""

    @property
    def is_empty(self) -> bool:
        """True if the chunk is empty"""
        return self.text == ""

    @staticmethod
    def empty() -> "TextChunk":
        """Returns an empty text chunk"""
        return TextChunk()


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
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    _slot_name: Optional[str] = None

    def __post_init__(self):
        if ":" in self.list_name:
            # list_name:slot_name
            self.list_name, self._slot_name = self.list_name.split(":", maxsplit=1)
        else:
            self._slot_name = self.list_name

    @property
    def slot_name(self) -> str:
        """Name of slot to put list value into."""
        assert self._slot_name is not None
        return self._slot_name


@dataclass
class Sentence(Sequence):
    """Sequence representing a complete sentence template."""

    text: Optional[str] = None
