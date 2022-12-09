from typing import Iterable, List

from .expression import Sentence
from .expression_listener import HassILExpressionListener


def parse_sentences(sentences: Iterable[str]) -> List[Sentence]:
    listener = HassILExpressionListener()
    listener.parse_sentences(sentences)
    return listener.sentences


def parse_sentence(sentence: str) -> Sentence:
    return parse_sentences([sentence])[0]
