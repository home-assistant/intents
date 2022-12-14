from typing import Iterable, List

from .expression import Sentence
from .expression_listener import HassILExpressionListener


def parse_sentences(texts: Iterable[str], keep_text: bool = False) -> List[Sentence]:
    listener = HassILExpressionListener()
    listener.parse_sentences(texts)
    if keep_text:
        for text, sentence in zip(texts, listener.sentences):
            sentence.text = text

    return listener.sentences


def parse_sentence(text: str, keep_text: bool = False) -> Sentence:
    sentence = parse_sentences([text])[0]
    if keep_text:
        sentence.text = text

    return sentence
