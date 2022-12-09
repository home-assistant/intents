from typing import Iterable, List, Optional

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker

from .expression import (
    NUMBER_PATTERN,
    NUMBER_RANGE_PATTERN,
    Expression,
    ListReference,
    Number,
    NumberRange,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    Word,
    remove_escapes,
    remove_quotes,
)
from .grammar.HassILGrammarLexer import HassILGrammarLexer
from .grammar.HassILGrammarListener import HassILGrammarListener
from .grammar.HassILGrammarParser import HassILGrammarParser

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
        group = self._pop_group()
        self.last_sequence.items.append(group)

    def enterOptional(self, ctx):
        self._sequences.append(GROUP_MARKER)

        # Start as a group, will convert to alternative at exit
        self._sequences.append(Sequence(type=SequenceType.GROUP))

    def exitOptional(self, ctx):
        optional = self._pop_group()

        if optional.type != SequenceType.ALTERNATIVE:
            if len(optional.items) > 1:
                # Wrap in group
                optional.items = [
                    Sequence(type=SequenceType.GROUP, items=optional.items)
                ]

            optional.type = SequenceType.ALTERNATIVE

        optional.items.append(Word.empty())
        self.last_sequence.items.append(optional)

    def enterAlt(self, ctx):
        sequence = self.last_sequence
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
        self.last_sequence.items.append(RuleReference(rule_name))

    def enterList(self, ctx):
        list_name = ctx.list_name().STRING().getText()
        self.last_sequence.items.append(ListReference(list_name))

    def enterWord(self, ctx: HassILGrammarParser.WordContext):
        word_text = ctx.STRING().getText().strip()
        word_text = remove_escapes(word_text)
        word_text = remove_quotes(word_text)

        match = NUMBER_PATTERN.match(word_text)
        if match is not None:
            item: Expression = Number(int(match[1]))
        else:
            match = NUMBER_RANGE_PATTERN.match(word_text)
            if match is not None:
                step_str = match.groupdict().get("step") or "1"
                item = NumberRange(
                    lower_bound=int(match[1]),
                    upper_bound=int(match[2]),
                    step=int(step_str),
                )
            else:
                item = Word(word_text)

        self.last_sequence.items.append(item)

    def parse_sentences(self, sentences: Iterable[str]):
        text = "\n".join(sentences) + "\n"
        parser = HassILGrammarParser(
            CommonTokenStream(HassILGrammarLexer(InputStream(text)))
        )
        walker = ParseTreeWalker()
        walker.walk(self, parser.document())

    @property
    def last_sequence(self) -> Sequence:
        assert self._sequences, "No target sequence"
        last_sequence = self._sequences[-1]
        assert last_sequence, "Invalid target sequence"
        return last_sequence

    def _pop_group(self) -> Sequence:
        assert len(self._sequences) > 1, "Bad sequence stack"
        item = self._sequences.pop()
        while self._sequences[-1] is not GROUP_MARKER:
            item = self._sequences.pop()

        assert item is not None, "Invalid last sequence"

        # Remove group marker
        marker = self._sequences.pop()
        assert marker is GROUP_MARKER, "Missing group marker"

        return item
