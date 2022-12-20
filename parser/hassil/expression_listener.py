"""Listener for converting ANTLR parse into Sentence expressions."""
from typing import Iterable, List, Optional

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker

from .expression import (
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    TextChunk,
)
from .grammar.HassILGrammarLexer import HassILGrammarLexer
from .grammar.HassILGrammarListener import HassILGrammarListener
from .grammar.HassILGrammarParser import HassILGrammarParser
from .util import normalize_text, remove_escapes

GROUP_MARKER = None


class HassILExpressionListener(HassILGrammarListener):
    """Listener that transforms ANTLR form into expressions."""

    def __init__(self) -> None:
        # List of sentences parsed so far
        self.sentences: List[Sentence] = []

        # Current sentence
        self._sentence: Optional[Sentence] = None

        # Current sequences being parsed.
        # The last sequence is the current target.
        # Groups of sequences and sub-sequences are separated with None.
        self._sequences: List[Optional[Sequence]] = []

    def enterSentence(self, ctx: HassILGrammarParser.SentenceContext):
        # Begin new sentence
        self._sentence = Sentence()
        self._sequences = [self._sentence]

    def exitSentence(self, ctx):
        # Complete sentence
        assert self._sentence is not None, "No sentence started"
        self.sentences.append(self._sentence)
        self._sentence = None
        self._sequences = []

    def enterGroup(self, ctx):
        # Begin new (group), not a sub-sequence
        self._sequences.append(GROUP_MARKER)
        self._sequences.append(Sequence(type=SequenceType.GROUP))

    def exitGroup(self, ctx):
        # Complete (group)
        group = self._pop_group()
        self.last_sequence.items.append(group)

    def enterOptional(self, ctx):
        # Begin new [optional], not a sub-sequence
        self._sequences.append(GROUP_MARKER)

        # Start as a group, will convert to alternative at exit
        self._sequences.append(Sequence(type=SequenceType.GROUP))

    def exitOptional(self, ctx):
        # Complete [optional], convert to alternative if necessary
        optional = self._pop_group()

        if optional.type != SequenceType.ALTERNATIVE:
            if len(optional.items) > 1:
                # Wrap in group
                optional.items = [
                    Sequence(type=SequenceType.GROUP, items=optional.items)
                ]

            optional.type = SequenceType.ALTERNATIVE

        # Optionals are just alternatives with an empty text chunk ("") as an option.
        optional.items.append(TextChunk.empty())
        self.last_sequence.items.append(optional)

    def enterAlt(self, ctx):
        # Encountered an alternative marker "|" inside a group or optional.
        # This is complex because the group/optional may already contain some items.
        sequence = self.last_parent_sequence
        if sequence.type != SequenceType.ALTERNATIVE:
            # Convert to alternative
            if sequence.items:
                # Wrap into a group
                old_items = sequence.items
                sequence.items = [Sequence(type=SequenceType.GROUP, items=old_items)]

            sequence.type = SequenceType.ALTERNATIVE

        # Start new group (sub-sequence)
        next_group = Sequence(type=SequenceType.GROUP)
        sequence.items.append(next_group)
        self._sequences.append(next_group)

    def enterRule(self, ctx: HassILGrammarParser.RuleContext):
        # <expansion_rule>
        rule_name = ctx.rule_name().STRING().getText()
        self.last_sequence.items.append(RuleReference(rule_name))

    def enterList(self, ctx: HassILGrammarParser.ListContext):
        # {slot_list}
        list_name = ctx.list_name().STRING().getText()
        self.last_sequence.items.append(ListReference(list_name))

    def enterText_chunk(self, ctx: HassILGrammarParser.Text_chunkContext):
        # Includes whitespace
        chunk_text = normalize_text(ctx.STRING().getText())
        chunk_text = remove_escapes(chunk_text)

        # Add to last sub-sequence
        self.last_sequence.items.append(TextChunk(chunk_text))

    def parse_sentences(self, sentences: Iterable[str]):
        """Parse multiple sentences separated by newlines."""
        text = "\n".join(sentences) + "\n"
        if text.strip():
            parser = HassILGrammarParser(
                CommonTokenStream(HassILGrammarLexer(InputStream(text)))
            )
            walker = ParseTreeWalker()
            walker.walk(self, parser.document())

    @property
    def last_sequence(self) -> Sequence:
        """Current sequence or sub-sequence target."""
        assert self._sequences, "No target sequence"
        last_sequence = self._sequences[-1]
        assert last_sequence, "Invalid target sequence"
        return last_sequence

    @property
    def last_parent_sequence(self) -> Sequence:
        """Current sequence target."""
        assert self._sequences, "No target sequence"

        # Locate last group marker to determine parent:
        # [parent, child, child, None, parent, ...]
        parent_sequence: Optional[Sequence] = None
        for sequence in reversed(self._sequences):
            if sequence is GROUP_MARKER:
                break

            parent_sequence = sequence

        assert parent_sequence, "No parent sequence"
        return parent_sequence

    def _pop_group(self) -> Sequence:
        """Remove sequences until a group marker is encountered."""
        assert len(self._sequences) > 1, "Bad sequence stack"
        item = self._sequences.pop()
        while self._sequences[-1] is not GROUP_MARKER:
            item = self._sequences.pop()

        assert item is not None, "Invalid last sequence"

        # Remove group marker
        marker = self._sequences.pop()
        assert marker is GROUP_MARKER, "Missing group marker"

        return item
