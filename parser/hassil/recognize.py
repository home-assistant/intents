import dataclasses
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Union

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

NUMBER_START = re.compile(r"^(-?[0-9]+).*$")

# TODO: Make this configurable
PUNCTUATION_END = re.compile(r"[.,;!?]$")

NON_WORD = re.compile(r"^\W+$")


class MissingListError(Exception):
    pass


class MissingRuleError(Exception):
    pass


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
    words: List[str] = field(default_factory=list)
    word_index: int = 0
    slot_lists: Dict[str, SlotList] = field(default_factory=dict)
    expansion_rules: Dict[str, Sentence] = field(default_factory=dict)
    skip_words: Set[str] = field(default_factory=set)
    entities: List[MatchEntity] = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        """True no words are left"""
        return not self.words

    def next_word(self, **kwargs) -> "MatchContext":
        return dataclasses.replace(
            self,
            words=self.words[1:],
            word_index=self.word_index + 1,
            **kwargs,
        )


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
                    words=words,
                    slot_lists=slot_lists,
                    expansion_rules=expansion_rules,
                    skip_words=skip_words,
                )
                sentence_contexts = _match_and_skip(context, intent_sentence)
                for sentence_context in sentence_contexts:
                    if sentence_context.is_match:
                        # Add fixed entities
                        for slot_name, slot_value in intent_data.slots.items():
                            sentence_context.entities.append(
                                MatchEntity(name=slot_name, value=slot_value)
                            )

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

    for match_context in _match_and_skip(context, sentence):
        if match_context.is_match:
            return match_context

    return None


def _match_and_skip(context: MatchContext, *args, **kwargs) -> Iterable[MatchContext]:
    """Match a sentence, then skip any skippable words at the end of input"""
    for match_context in match_expression(context, *args, *kwargs):
        has_words_left = False
        for word in match_context.words:
            word_text = _preprocess_word(word)
            if (word_text not in context.skip_words) and _is_word(word_text):
                # Can't skip a word
                has_words_left = True
                break

        if not has_words_left:
            yield dataclasses.replace(match_context, words=[])


def match_expression(
    context: MatchContext, expression: Expression
) -> Iterable[MatchContext]:
    """Yield matching contexts for an expresion"""
    if isinstance(expression, Word):
        word: Word = expression
        if word.is_empty:
            # Skip template word
            yield context

        if context.words:
            if _is_word_match(context.words[0], word.text):
                # Word match
                yield context.next_word()
            else:
                word_text = _preprocess_word(context.words[0])
                if (word_text in context.skip_words) or not _is_word(word_text):
                    # Skip input word
                    yield from match_expression(context.next_word(), expression)

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

            if context.words:
                # Any value may match
                for slot_value in text_list.values:
                    value_contexts = match_expression(
                        dataclasses.replace(context), slot_value.text_in
                    )

                    for value_context in value_contexts:
                        # Capture words for entity
                        entity_words = context.words[
                            : value_context.word_index - context.word_index
                        ]
                        value_context.entities.append(
                            MatchEntity(
                                name=list_ref.slot_name,
                                value=slot_value.value_out,
                                words=[_preprocess_word(word) for word in entity_words],
                                words_raw=entity_words,
                                word_start_index=context.word_index,
                                word_stop_index=value_context.word_index,
                            )
                        )
                        yield value_context

        elif isinstance(slot_list, RangeSlotList):
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
                                name=list_ref.slot_name,
                                value=word_number,
                                words=[_preprocess_word(word) for word in entity_words],
                                words_raw=entity_words,
                                word_start_index=context.word_index,
                                word_stop_index=context.word_index + 1,
                            )
                        )

                        # Skip over number
                        yield context.next_word()

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

    elif isinstance(expression, Number):
        # N
        number: Number = expression
        if context.words:
            word_number = _extract_number(context.words[0])
            if (word_number is not None) and (word_number == number.number):
                yield context.next_word()

    elif isinstance(expression, NumberRange):
        # N..M
        number_range: NumberRange = expression
        if context.words:
            word_number = _extract_number(context.words[0])
            if (word_number is not None) and (word_number in number_range):
                yield context.next_word()

    else:
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


def _is_word(text: str) -> bool:
    return bool(text) and (not NON_WORD.match(text))
