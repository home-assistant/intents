"""Methods for recognizing intents from text."""

import dataclasses
import itertools
import re
from dataclasses import dataclass, field
from os.path import commonprefix
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .expression import (
    Expression,
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    TextChunk,
)
from .intents import Intent, Intents, RangeSlotList, SlotList, TextSlotList
from .util import normalize_text

NUMBER_START = re.compile(r"^(\s*-?[0-9]+)")

NON_WORD = re.compile(r"^(\W+\s*)")


class MissingListError(Exception):
    """Error when a {slot_list} is missing."""


class MissingRuleError(Exception):
    """Error when an <expansion_rule> is missing."""


@dataclass
class MatchEntity:
    """Named entity that has been matched from a {slot_list}"""

    name: str
    """Name of the entity."""

    value: Any
    """Value of the entity."""


@dataclass
class MatchContext:
    """Context passed to match_expression."""

    text: str
    """Input text remaining to be processed."""

    text_index: int = 0
    """Index of text currently being processed."""

    slot_lists: Dict[str, SlotList] = field(default_factory=dict)
    """Available slot lists mapped by name."""

    expansion_rules: Dict[str, Sentence] = field(default_factory=dict)
    """Available expansion rules mapped by name."""

    skip_words: List[re.Pattern] = field(default_factory=list)
    """Words that can be skipped during recognition."""

    entities: List[MatchEntity] = field(default_factory=list)
    """Entities that have been found in input text."""

    @property
    def is_match(self) -> bool:
        """True if no words are left"""
        return not self.text


@dataclass
class RecognizeResult:
    """Result of recognition."""

    intent: Intent
    """Matched intent"""

    entities: Dict[str, MatchEntity] = field(default_factory=dict)
    """Matched entities mapped by name."""

    entities_list: List[MatchEntity] = field(default_factory=list)
    """Matched entities as a list (duplicates allowed)."""


def recognize(
    text: str,
    intents: Intents,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    skip_words: Optional[Iterable[str]] = None,
) -> Optional[RecognizeResult]:
    """Return the first match of input text/words against a collection of intents."""
    text = normalize_text(text)

    if slot_lists is None:
        slot_lists = intents.slot_lists
    else:
        # Combine with intents
        slot_lists = {**intents.slot_lists, **slot_lists}

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = intents.expansion_rules
    else:
        # Combine rules
        expansion_rules = {**intents.expansion_rules, **expansion_rules}

    if skip_words is None:
        skip_words = intents.skip_words
    else:
        # Combine skip words
        skip_words = itertools.chain(skip_words, intents.skip_words)

    # Check sentence against each intent.
    # This should eventually be done in parallel.
    for intent in intents.intents.values():
        for intent_data in intent.data:
            for intent_sentence in intent_data.sentences:
                # Create initial context
                context = MatchContext(
                    text=text,
                    slot_lists=slot_lists,
                    expansion_rules=expansion_rules,
                    skip_words=_prepare_skip_words(skip_words),
                )
                sentence_contexts = _match_and_skip(context, intent_sentence)
                for sentence_context in sentence_contexts:
                    if sentence_context.is_match:
                        # Add fixed entities
                        for slot_name, slot_value in intent_data.slots.items():
                            sentence_context.entities.append(
                                MatchEntity(name=slot_name, value=slot_value)
                            )

                        # Return the first match
                        return RecognizeResult(
                            intent,
                            {
                                entity.name: entity
                                for entity in sentence_context.entities
                            },
                            sentence_context.entities,
                        )

    return None


def is_match(
    text: str,
    sentence: Sentence,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    skip_words: Optional[Iterable[str]] = None,
    entities: Optional[Dict[str, Any]] = None,
) -> Optional[MatchContext]:
    """Return the first match of input text/words against a sentence expression."""
    text = normalize_text(text)

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = {}

    if skip_words is None:
        skip_words = []
    else:
        skip_words = sorted(skip_words, key=len, reverse=True)

    context = MatchContext(
        text=text,
        slot_lists=slot_lists,
        expansion_rules=expansion_rules,
        skip_words=_prepare_skip_words(skip_words),
    )

    for match_context in _match_and_skip(context, sentence):
        if match_context.is_match:
            return match_context

    return None


def _prepare_skip_words(skip_words: Iterable[str]) -> List[re.Pattern]:
    """Convert skip word strings to regex patterns."""
    patterns: List[re.Pattern] = []
    for skip_word in skip_words:
        skip_word = normalize_text(skip_word)
        patterns.append(re.compile(rf"^{re.escape(skip_word)}\b"))

    return patterns


def _match_and_skip(context: MatchContext, *args, **kwargs) -> Iterable[MatchContext]:
    """Match a sentence, then skip any skippable words at the end of input"""
    for match_context in match_expression(context, *args, *kwargs):
        while match_context.text:
            can_skip, match_context.text = _skip(match_context.text, context.skip_words)
            if not can_skip:
                break

        yield match_context


def match_expression(
    context: MatchContext, expression: Expression
) -> Iterable[MatchContext]:
    """Yield matching contexts for an expresion"""
    if isinstance(expression, TextChunk):
        chunk: TextChunk = expression
        if chunk.is_empty:
            # Skip template chunk
            yield context

        context_text_left = context.text
        chunk_text_left = chunk.text

        while chunk_text_left:
            prefix = commonprefix((context_text_left, chunk_text_left))

            if prefix:
                # Common prefix
                context_text_left = context_text_left[len(prefix) :]
                chunk_text_left = chunk_text_left[len(prefix) :]
            else:
                can_skip, context_text_left = _skip(
                    context_text_left, context.skip_words
                )

                if not can_skip:
                    break

        if not chunk_text_left:
            yield dataclasses.replace(context, text=context_text_left)

    elif isinstance(expression, Sequence):
        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            # Any may match (words | in | alternative)
            for item in seq.items:
                yield from match_expression(context, item)

        elif seq.type == SequenceType.GROUP:
            # All must match (words in group)
            # NOTE: [optional] = (optional | )
            if seq.items:
                group_contexts = [context]
                for item in seq.items:
                    # Next step
                    group_contexts = [
                        item_context
                        for group_context in group_contexts
                        for item_context in match_expression(group_context, item)
                    ]
                    if not group_contexts:
                        break

                for group_context in group_contexts:
                    yield group_context
        else:
            raise ValueError(f"Unexpected sequence type: {seq}")

    elif isinstance(expression, ListReference):
        # {list}
        list_ref: ListReference = expression
        if (not context.slot_lists) or (list_ref.list_name not in context.slot_lists):
            raise MissingListError(f"Missing slot list {{{list_ref.list_name}}}")

        slot_list = context.slot_lists[list_ref.list_name]
        if isinstance(slot_list, TextSlotList):
            text_list: TextSlotList = slot_list

            if context.text:
                # Any value may match
                for slot_value in text_list.values:
                    value_contexts = match_expression(
                        dataclasses.replace(context), slot_value.text_in
                    )

                    for value_context in value_contexts:
                        value_context.entities.append(
                            MatchEntity(
                                name=list_ref.slot_name, value=slot_value.value_out
                            )
                        )
                        yield value_context

        elif isinstance(slot_list, RangeSlotList):
            # List that represents a number range.
            # Numbers must currently be digits ("1" not "one").
            range_list: RangeSlotList = slot_list
            if context.text:
                number_match = NUMBER_START.match(context.text)
                if number_match is not None:
                    number_text = number_match[1]
                    word_number = int(number_text)
                    if range_list.step == 1:
                        # Unit step
                        in_range = range_list.start <= word_number <= range_list.stop
                    else:
                        # Non-unit step
                        in_range = word_number in range(
                            range_list.start, range_list.stop + 1, range_list.step
                        )

                    if in_range:
                        context.entities.append(
                            MatchEntity(name=list_ref.slot_name, value=word_number)
                        )

                        yield dataclasses.replace(
                            context, text=context.text[len(number_text) :].lstrip()
                        )

        else:
            raise ValueError(f"Unexpected slot list type: {slot_list}")

    elif isinstance(expression, RuleReference):
        # <rule>
        rule_ref: RuleReference = expression
        if (not context.expansion_rules) or (
            rule_ref.rule_name not in context.expansion_rules
        ):
            raise MissingRuleError(f"Missing expansion rule <{rule_ref.rule_name}>")

        yield from match_expression(
            context, context.expansion_rules[rule_ref.rule_name]
        )
    else:
        raise ValueError(f"Unexpected expression: {expression}")


def _skip(text: str, skip_words: Iterable[re.Pattern]) -> Tuple[bool, str]:
    """Skip over skip/non-words."""
    # Skip words
    for skip_word in skip_words:
        skip_word_match = skip_word.match(text)
        if skip_word_match is not None:
            text = text[len(skip_word_match[0]) :].lstrip()
            return True, text

    # Non-words
    nonword_match = NON_WORD.match(text)
    if nonword_match is not None:
        # Skip nonword parts
        nonword_text = nonword_match[1]
        text = text[len(nonword_text) :]
        return True, text

    return False, text
