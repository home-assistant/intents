from typing import Iterable, List, Optional

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker

from .expression import (
    Sentence,
    Sequence,
    SequenceType,
    RuleReference,
    ListReference,
    Number,
    NUMBER_RANGE_PATTERN,
    Word,
    remove_escapes,
    remove_quotes,
)
from .grammar.HassILGrammarListener import HassILGrammarListener
from .grammar.HassILGrammarParser import HassILGrammarParser
from .grammar.HassILGrammarLexer import HassILGrammarLexer

GROUP_MARKER = None


class HassILExpressionListener(HassILGrammarListener):
    def __init__(self):
        self.sentences: List[Sentence] = []
        self._sentence: Optional[Sentence] = None
        self._sequences: List[Optional[Sequence]] = []

    def enterSentence(self, ctx: HassILGrammarParser.SentenceContext):
        self._sentence = Sentence()
        self._sequences = [self._sentence]

    def exitSentence(self, ctx):
        assert self._sentence is not None, "No sentence started"
        self.sentences.append(self._sentence)
        self._sentence = None
        self._sequences = []

    def enterGroup(self, ctx):
        self._sequences.append(GROUP_MARKER)
        self._sequences.append(Sequence(type=SequenceType.GROUP))

    def exitGroup(self, ctx):
        group = self._sequences.pop()
        while self._sequences[-1] is not GROUP_MARKER:
            group = self._sequences.pop()

        # Remove group marker
        self._sequences.pop()

        self._sequences[-1].items.append(group)

    def enterOptional(self, ctx):
        self._sequences.append(GROUP_MARKER)
        self._sequences.append(Sequence(type=SequenceType.ALTERNATIVE))

    def exitOptional(self, ctx):
        optional = self._sequences.pop()
        while self._sequences[-1] is not GROUP_MARKER:
            optional = self._sequences.pop()

        # Remove group marker
        self._sequences.pop()

        optional.items.append(Word.empty())
        self._sequences[-1].items.append(optional)

    def enterAlt(self, ctx):
        sequence = self._sequences[-1]
        if sequence.type != SequenceType.ALTERNATIVE:
            # Convert to alternative
            if sequence.items:
                # Wrap into a group
                old_items = sequence.items
                sequence.items = [Sequence(type=SequenceType.GROUP, items=old_items)]

            sequence.type = SequenceType.ALTERNATIVE

        # Start new group
        next_group = Sequence(type=SequenceType.GROUP)
        sequence.items.append(next_group)
        self._sequences.append(next_group)

    def enterRule(self, ctx: HassILGrammarParser.RuleContext):
        rule_name = ctx.rule_name().STRING().getText()
        self._sequences[-1].items.append(RuleReference(rule_name))

    def enterList(self, ctx):
        list_name = ctx.list_name().STRING().getText()
        self._sequences[-1].items.append(ListReference(list_name))

    def enterWord(self, ctx: HassILGrammarParser.WordContext):
        word_text = ctx.STRING().getText().strip()
        word_text = remove_escapes(word_text)
        word_text = remove_quotes(word_text)
        self._sequences[-1].items.append(Word(word_text))

    def parse_sentences(self, sentences: Iterable[str]):
        text = "\n".join(sentences)
        parser = HassILGrammarParser(
            CommonTokenStream(HassILGrammarLexer(InputStream(text)))
        )
        walker = ParseTreeWalker()
        walker.walk(self, parser.sentence())
