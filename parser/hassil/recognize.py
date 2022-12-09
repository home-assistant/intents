import dataclasses
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .expression import (
    Expression,
    ListReference,
    Number,
    NumberRange,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    Word,
)
from .intents import Intent, Intents, RangeSlotList, SlotList, TextSlotList

NUMBER_START = re.compile("^(-?[0-9]+).*$")

# TODO: Make this configurable
PUNCTUATION_END = re.compile("[.,;!?]$")


class MissingListError(Exception):
    pass


class MissingRuleError(Exception):
    pass


class MatchState(Enum):
    SUCCESS = auto()
    FAIL = auto()
    SKIP = auto()


@dataclass
class MatchEntity:
    name: str
    value: Any
    words: Optional[List[str]] = None
    words_raw: Optional[List[str]] = None
    word_start_index: Optional[int] = None
    word_stop_index: Optional[int] = None


@dataclass
class MatchContext:
    state: Optional[MatchState] = None
    words: List[str] = field(default_factory=list)
    word_index: int = 0
    slot_lists: Dict[str, SlotList] = field(default_factory=dict)
    expansion_rules: Dict[str, Sentence] = field(default_factory=dict)
    skip_words: Set[str] = field(default_factory=set)
    entities: List[MatchEntity] = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        """True if last match was a success and no words are left"""
        return (self.state == MatchState.SUCCESS) and (not self.words)


@dataclass
class RecognizeResult:
    intent: Intent
    entities: Dict[str, MatchEntity] = field(default_factory=dict)
    entities_list: List[MatchEntity] = field(default_factory=list)


def recognize(
    text_or_words: Union[str, List[str]],
    intents: Intents,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    skip_words: Optional[Set[str]] = None,
) -> Optional[RecognizeResult]:
    if isinstance(text_or_words, str):
        # TODO: tokenize for language
        words = _tokenize_sentence(_preprocess_sentence(text_or_words))
    else:
        words = text_or_words

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
        skip_words = set.union(skip_words, intents.skip_words)

    # Preprocess skip words
    skip_words = {_preprocess_word(word) for word in skip_words}

    for intent in intents.intents.values():
        for intent_data in intent.data:
            for intent_sentence in intent_data.sentences:
                context = MatchContext(
                    state=MatchState.SKIP,
                    words=words,
                    slot_lists=slot_lists,
                    expansion_rules=expansion_rules,
                    skip_words=skip_words,
                )
                context = _match_and_skip(context, intent_sentence)

                if context.is_match:
                    # Add fixed entities
                    for slot_name, slot_value in intent_data.slots.items():
                        context.entities.append(
                            MatchEntity(name=slot_name, value=slot_value)
                        )

                    return RecognizeResult(
                        intent,
                        {entity.name: entity for entity in context.entities},
                        context.entities,
                    )

    return None


def is_match(
    text_or_words: Union[str, List[str]],
    sentence: Sentence,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    skip_words: Optional[Set[str]] = None,
    entities: Optional[Dict[str, Any]] = None,
) -> Optional[MatchContext]:
    if isinstance(text_or_words, str):
        # TODO: tokenize for language
        words = _tokenize_sentence(_preprocess_sentence(text_or_words))
    else:
        words = text_or_words

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = {}

    if skip_words is None:
        skip_words = set()

    context = MatchContext(
        words=words,
        slot_lists=slot_lists,
        expansion_rules=expansion_rules,
        skip_words=skip_words,
    )

    context = _match_and_skip(context, sentence)

    return context if context.state == MatchState.SUCCESS else None


def _match_and_skip(context: MatchContext, *args, **kwargs) -> MatchContext:
    """Match a sentence, then skip any skippable words at the end of input"""
    context.state = MatchState.SKIP

    while context.state == MatchState.SKIP:
        context = match_expression(context, *args, **kwargs)

    assert context.state in {MatchState.SUCCESS, MatchState.FAIL}
    if context.state == MatchState.SUCCESS:
        # Allow skippable words at the end
        while context.words:
            if _preprocess_word(context.words[0]) not in context.skip_words:
                # Non-skippable word at end
                context.state = MatchState.FAIL
                return context

            context.words = context.words[1:]
            context.word_index += 1

    context.state = MatchState.FAIL if context.words else MatchState.SUCCESS
    return context


def match_expression(context: MatchContext, expression: Expression) -> MatchContext:
    if isinstance(expression, Word):
        word: Word = expression
        if word.is_empty:
            # Skip template word
            context.state = MatchState.SUCCESS
            return context

        if context.words:
            if _is_word_match(context.words[0], word.text):
                # Word match
                context.state = MatchState.SUCCESS
                context.words = context.words[1:]
                context.word_index += 1
                return context

            if context.words[0] in context.skip_words:
                # Skip input word
                context.state = MatchState.SKIP
                context.words = context.words[1:]
                context.word_index += 1
                return context

        # Failed to match word
        context.state = MatchState.FAIL
        return context

    if isinstance(expression, Sequence):
        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            # Any may match (words | in | alternative)
            context.state = MatchState.FAIL
            for item in seq.items:
                # Handle input word skips
                item_context = dataclasses.replace(context, state=MatchState.SKIP)
                while item_context.state == MatchState.SKIP:
                    item_context = match_expression(item_context, item)

                if item_context.state == MatchState.SUCCESS:
                    # Any may match
                    return item_context

        if seq.type == SequenceType.GROUP:
            # All must match (words in group)
            # NOTE: [optional] = (optional | )
            group_context = dataclasses.replace(context)

            for item in seq.items:
                # Handle input word skips
                group_context.state = MatchState.SKIP
                while group_context.state == MatchState.SKIP:
                    group_context = match_expression(group_context, item)

                if group_context.state != MatchState.SUCCESS:
                    # All must match
                    context.state = MatchState.FAIL
                    return context

            # All matched
            group_context.state = MatchState.SUCCESS
            return group_context

    if isinstance(expression, ListReference):
        # {list}
        list_ref: ListReference = expression
        if (not context.slot_lists) or (list_ref.list_name not in context.slot_lists):
            raise MissingListError(f"Missing slot list {list_ref.list_name}")

        slot_list = context.slot_lists[list_ref.list_name]
        if isinstance(slot_list, TextSlotList):
            text_list: TextSlotList = slot_list

            if context.words:
                # Any value may match
                for slot_value in text_list.values:
                    value_context = match_expression(
                        dataclasses.replace(context), slot_value.text_in
                    )

                    if value_context.state == MatchState.SUCCESS:
                        entity_words = context.words[
                            : value_context.word_index - context.word_index
                        ]
                        value_context.entities.append(
                            MatchEntity(
                                name=list_ref.list_name,
                                value=slot_value.value_out,
                                words=[_preprocess_word(word) for word in entity_words],
                                words_raw=entity_words,
                                word_start_index=context.word_index,
                                word_stop_index=value_context.word_index,
                            )
                        )
                        return value_context

            # No values matched
            context.state = MatchState.FAIL
            return context

        if isinstance(slot_list, RangeSlotList):
            range_list: RangeSlotList = slot_list
            if context.words:
                number_match = False
                word_number = _extract_number(context.words[0])
                if word_number is not None:
                    if range_list.step == 1:
                        # Unit step
                        number_match = (
                            range_list.start <= word_number <= range_list.stop
                        )
                    else:
                        # Non-unit step
                        number_match = word_number in range(
                            range_list.start, range_list.stop + 1, range_list.step
                        )

                    if number_match:
                        entity_words = [context.words[0]]
                        context.entities.append(
                            MatchEntity(
                                name=list_ref.list_name,
                                value=word_number,
                                words=[_preprocess_word(word) for word in entity_words],
                                words_raw=entity_words,
                                word_start_index=context.word_index,
                                word_stop_index=context.word_index + 1,
                            )
                        )

                        # Skip over number
                        context.words = context.words[1:]
                        context.word_index += 1

                        context.state = MatchState.SUCCESS
                        return context

            # No values matched
            context.state = MatchState.FAIL
            return context

        raise ValueError(f"Unexpected slot list type: {slot_list}")

    if isinstance(expression, RuleReference):
        # <rule>
        rule_ref: RuleReference = expression
        if (not context.expansion_rules) or (
            rule_ref.rule_name not in context.expansion_rules
        ):
            raise MissingRuleError(f"Missing expansion rule {rule_ref.rule_name}")

        return match_expression(context, context.expansion_rules[rule_ref.rule_name])

    if isinstance(expression, Number):
        # N
        number: Number = expression
        if context.words:
            word_number = _extract_number(context.words[0])
            if (word_number is not None) and (word_number == number.number):
                context.state = MatchState.SUCCESS
                context.words = context.words[1:]
                context.word_index += 1
                return context

        context.state = MatchState.FAIL
        return context

    if isinstance(expression, NumberRange):
        # N..M
        number_range: NumberRange = expression
        if context.words:
            word_number = _extract_number(context.words[0])
            if (word_number is not None) and (word_number in number_range):
                context.state = MatchState.SUCCESS
                context.words = context.words[1:]
                context.word_index += 1
                return context

        context.state = MatchState.FAIL
        return context

    raise ValueError(f"Unexpected expression: {expression}")


def _tokenize_sentence(text: str) -> List[str]:
    """Split sentence into tokens (words)"""
    return text.split()


def _preprocess_sentence(text: str) -> str:
    return text.strip()


def _preprocess_word(text: str) -> str:
    text = text.strip().casefold()
    text = PUNCTUATION_END.sub("", text)
    return text


def _is_word_match(text1: str, text2: str) -> bool:
    """True if words are considered the same"""
    text1 = _preprocess_word(text1)
    text2 = _preprocess_word(text2)

    return text1 == text2


def _extract_number(text: str) -> Optional[int]:
    """Extracts an integer from any string that starts with at least one digit"""
    match = NUMBER_START.match(text)
    if match is not None:
        return int(match[1])

    return None
