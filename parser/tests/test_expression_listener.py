"""Tests for HassILExpressionListener"""
from hassil import (
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    TextChunk,
    parse_sentences,
)


def test_just_words():
    assert parse_sentences(["this is a test"]) == [s([tc("this is a test")])]


def test_group():
    assert parse_sentences(["(this is a test)"]) == [
        s(
            [
                grp(
                    [tc("this is a test")],
                )
            ]
        )
    ]


def test_optional():
    assert parse_sentences(["this is [a] test"]) == [
        s(
            [
                tc("this is"),
                alt(
                    [tc("a"), TextChunk.empty()],
                ),
                tc("test"),
            ]
        )
    ]


def test_optional_nested():
    assert parse_sentences(["this [is [a]] test"]) == [
        s(
            [
                tc("this"),
                alt(
                    [
                        grp([tc("is"), alt([tc("a"), TextChunk.empty()])]),
                        TextChunk.empty(),
                    ]
                ),
                tc("test"),
            ]
        )
    ]


def test_alternative():
    assert parse_sentences(["this is (a | the) test"]) == [
        s(
            [
                tc("this is"),
                alt(
                    [grp([tc("a")]), grp([tc("the")])],
                ),
                tc("test"),
            ]
        )
    ]


def test_alternative_multiple_words():
    assert parse_sentences(["this is (a bigger | the biggest) test"]) == [
        s(
            [
                tc("this is"),
                alt(
                    [
                        grp(
                            [tc("a bigger")],
                        ),
                        grp(
                            [tc("the biggest")],
                        ),
                    ],
                ),
                tc("test"),
            ]
        )
    ]


def test_alternative_what():
    assert parse_sentences(["(what | what's | whats | what is)"]) == [
        s(
            [
                alt(
                    [
                        grp(
                            [tc("what")],
                        ),
                        grp(
                            [tc("what's")],
                        ),
                        grp(
                            [tc("whats")],
                        ),
                        grp(
                            [tc("what is")],
                        ),
                    ],
                ),
            ]
        )
    ]


def test_list_reference():
    assert parse_sentences(["this is a {test}"]) == [
        s([tc("this is a"), ListReference("test")])
    ]


def test_list_reference_prefix_suffix():
    assert parse_sentences(["this is a pre'{test}-post"]) == [
        s([tc("this is a pre'"), ListReference("test"), tc("-post")])
    ]


def test_rule_reference():
    assert parse_sentences(["this is a <test>"]) == [
        s([tc("this is a"), RuleReference("test")])
    ]


def test_escape():
    assert parse_sentences(["this \\[is\\] a \\{test\\}"]) == [
        s([tc("this [is] a {test}")])
    ]


# -----------------------------------------------------------------------------


def s(items):
    return Sentence(items=items)


def tc(text):
    return TextChunk(text)


def grp(items):
    return Sequence(type=SequenceType.GROUP, items=items)


def alt(items):
    return Sequence(type=SequenceType.ALTERNATIVE, items=items)
