"""Tests for HassILExpressionListener"""
from hassil import (
    parse_sentences,
    Sentence,
    Word,
    Sequence,
    SequenceType,
    ListReference,
    RuleReference,
)


def test_just_words():
    assert parse_sentences(["this is a test"]) == [
        s([w("this"), w("is"), w("a"), w("test")])
    ]


def test_group():
    assert parse_sentences(["(this is a test)"]) == [
        s(
            [
                grp(
                    [w("this"), w("is"), w("a"), w("test")],
                )
            ]
        )
    ]


def test_optional():
    assert parse_sentences(["this is [a] test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [w("a"), Word.empty()],
                ),
                w("test"),
            ]
        )
    ]


def test_alternative():
    assert parse_sentences(["this is (a | the) test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [grp([w("a")]), grp([w("the")])],
                ),
                w("test"),
            ]
        )
    ]


def test_alternative_multiple_words():
    assert parse_sentences(["this is (a bigger | the biggest) test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [
                        grp(
                            [w("a"), w("bigger")],
                        ),
                        grp(
                            [w("the"), w("biggest")],
                        ),
                    ],
                ),
                w("test"),
            ]
        )
    ]


def test_list_reference():
    assert parse_sentences(["this is a {test}"]) == [
        s([w("this"), w("is"), w("a"), ListReference("test")])
    ]


def test_rule_reference():
    assert parse_sentences(["this is a <test>"]) == [
        s([w("this"), w("is"), w("a"), RuleReference("test")])
    ]


def test_escape():
    assert parse_sentences(["this \\[is\\] a \\{test\\}"]) == [
        s([w("this"), w("[is]"), w("a"), w("{test}")])
    ]


def test_quotes():
    assert parse_sentences(['this "[is]" a "{test}"']) == [
        s([w("this"), w("[is]"), w("a"), w("{test}")])
    ]


def test_escape_in_quotes():
    """Test escaped double quotes inside double quotes"""
    assert parse_sentences(['this is a "\\"test\\""']) == [
        s([w("this"), w("is"), w("a"), w('"test"')])
    ]


# -----------------------------------------------------------------------------


def s(items):
    return Sentence(items=items)


def w(text):
    return Word(text)


def grp(items):
    return Sequence(type=SequenceType.GROUP, items=items)


def alt(items):
    return Sequence(type=SequenceType.ALTERNATIVE, items=items)
