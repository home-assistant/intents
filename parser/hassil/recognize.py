import re
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union

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
from .parse import parse_sentence

NUMBER_START = re.compile("^(-?[0-9]+).*$")

# TODO: Make this configuration
PUNCTUATION_END = re.compile("[.,;!?]$")


class MissingListError(Exception):
    pass


class MissingRuleError(Exception):
    pass


class MatchState(Enum):
    SUCCESS = auto()
    FAIL = auto()
    SKIP = auto()


# def recognize(
#     text: str,
#     intents: Intents,
#     extra_lists: Optional[Dict[str, List[str]]] = None,
# ):
#     # TODO: tokenize for language
#     words = text.strip().split()
#     if extra_lists is None:
#         extra_lists = {}

#     for intent_name, intent in intents.intents.items():
#         pass


def is_match(
    text_or_words: Union[str, List[str]],
    sentence: Sentence,
    slot_lists: Optional[Dict[str, List[Sentence]]] = None,
    expansion_rules: Optional[Dict[str, Sentence]] = None,
    skip_words: Optional[Set[str]] = None,
) -> bool:
    if isinstance(text_or_words, str):
        # TODO: tokenize for language
        words = _tokenize_sentence(_preprocess_sentence(text_or_words))
    else:
        words = text_or_words

    if isinstance(sentence, str):
        sentence = parse_sentence(sentence)

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = {}

    if skip_words is None:
        skip_words = set()

    state, _words = _is_match(words, sentence, slot_lists, expansion_rules, skip_words)
    return state == MatchState.SUCCESS


def _is_match(
    words: List[str],
    expression: Expression,
    slot_lists: Dict[str, List[Sentence]],
    expansion_rules: Dict[str, Sentence],
    skip_words: Set[str],
) -> Tuple[MatchState, Optional[List[str]]]:
    if isinstance(expression, Word):
        word: Word = expression
        if word.is_empty:
            # Skip template word
            return MatchState.SUCCESS, words

        if words:
            if _is_word_match(words[0], word.text):
                # Word match
                return MatchState.SUCCESS, words[1:]

            if _preprocess_word(words[0]) in skip_words:
                # Skip input word
                return MatchState.SKIP, words[1:]

        return MatchState.FAIL, None

    if isinstance(expression, Sequence):
        state = MatchState.SKIP
        words_left: Optional[List[str]] = None

        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            # Any may match (words | in | alternative)
            for item in seq.items:
                words_left = words

                # Handle input word skips
                while state == MatchState.SKIP:
                    assert words_left is not None
                    state, words_left = _is_match(
                        words_left, item, slot_lists, expansion_rules, skip_words
                    )

                if state == MatchState.SUCCESS:
                    return MatchState.SUCCESS, words_left

            return MatchState.FAIL, None

        if seq.type == SequenceType.GROUP:
            # All must match (words in group)
            # NOTE: [optional] = (optional | )
            words_left = words
            for item in seq.items:

                # Handle input word skips
                while state == MatchState.SKIP:
                    assert words_left is not None
                    state, words_left = _is_match(
                        words_left, item, slot_lists, expansion_rules, skip_words
                    )

                if state != MatchState.SUCCESS:
                    return MatchState.FAIL, None

            return MatchState.SUCCESS, words_left

    if isinstance(expression, ListReference):
        # {list}
        list_ref: ListReference = expression
        if (not slot_lists) or (list_ref.list_name not in slot_lists):
            raise MissingListError(f"Missing slot list {list_ref.list_name}")

        list_values = slot_lists[list_ref.list_name]
        return _is_match(
            words,
            Sequence(type=SequenceType.ALTERNATIVE, items=list_values),
            slot_lists,
            expansion_rules,
            skip_words,
        )

    if isinstance(expression, RuleReference):
        # <rule>
        rule_ref: RuleReference = expression
        if (not expansion_rules) or (rule_ref.rule_name not in expansion_rules):
            raise MissingRuleError(f"Missing expansion rule {rule_ref.rule_name}")

        return _is_match(
            words,
            expansion_rules[rule_ref.rule_name],
            slot_lists,
            expansion_rules,
            skip_words,
        )

    if isinstance(expression, Number):
        # N
        number: Number = expression
        if words:
            word_number = _extract_number(words[0])
            if (word_number is not None) and (word_number == number.number):
                return MatchState.SUCCESS, words[1:]

        return MatchState.FAIL, None

    if isinstance(expression, NumberRange):
        # N..M
        number_range: NumberRange = expression
        if words:
            word_number = _extract_number(words[0])
            if (word_number is not None) and (word_number in number_range):
                return MatchState.SUCCESS, words[1:]

        return MatchState.FAIL, None

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
