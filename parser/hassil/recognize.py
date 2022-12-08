from typing import List, Optional, Dict, Union, Tuple

from .expression import (
    Sequence,
    Sentence,
    SequenceType,
    Word,
    ListReference,
    RuleReference,
    Expression,
)
from .intents import Intents
from .parse import parse_sentence


class MissingListError(Exception):
    pass


class MissingRuleError(Exception):
    pass


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
) -> bool:
    if isinstance(text_or_words, str):
        # TODO: tokenize for language
        words = text_or_words.split()
    else:
        words = text_or_words

    if isinstance(sentence, str):
        sentence = parse_sentence(sentence)

    if slot_lists is None:
        slot_lists = {}

    if expansion_rules is None:
        expansion_rules = {}

    success, _words = _is_match(words, sentence, slot_lists, expansion_rules)
    return success


def _is_match(
    words: List[str],
    expression: Expression,
    slot_lists: Dict[str, List[Sentence]] = None,
    expansion_rules: Dict[str, Sentence] = None,
) -> Tuple[bool, Optional[List[str]]]:
    if isinstance(expression, Word):
        word: Word = expression
        if word.is_empty:
            # Can skip word
            return True, words

        if words and (words[0] == word.text):
            return True, words[1:]

        return False, None

    if isinstance(expression, Sequence):
        words_left: Optional[List[str]] = None

        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            # Any may match
            for item in seq.items:
                success, words_left = _is_match(
                    words, item, slot_lists, expansion_rules
                )
                if success:
                    return True, words_left

            return False, None

        if seq.type == SequenceType.GROUP:
            # All must match
            words_left = words
            for item in seq.items:
                assert words_left is not None
                success, words_left = _is_match(
                    words_left, item, slot_lists, expansion_rules
                )
                if not success:
                    return False, None

            return True, words_left

    if isinstance(expression, ListReference):
        list_ref: ListReference = expression
        if (not slot_lists) or (list_ref.list_name not in slot_lists):
            raise MissingListError(f"Missing slot list {list_ref.list_name}")

        list_values = slot_lists[list_ref.list_name]
        return _is_match(
            words,
            Sequence(type=SequenceType.ALTERNATIVE, items=list_values),
            slot_lists,
            expansion_rules,
        )

    if isinstance(expression, RuleReference):
        rule_ref: RuleReference = expression
        if (not expansion_rules) or (rule_ref.rule_name not in expansion_rules):
            raise MissingRuleError(f"Missing expansion rule {rule_ref.rule_name}")

        return _is_match(
            words,
            expansion_rules[rule_ref.rule_name],
            slot_lists,
            expansion_rules,
        )

    raise ValueError(f"Unexpected expression: {expression}")
